"""
RedisJobStore - Implementación de JobStore usando Redis.

Permite persistir jobs de APScheduler en Redis para sobrevivir reinicios.
"""

import pickle
from datetime import datetime, timezone
from typing import List, Optional

from apscheduler.job import Job
from apscheduler.jobstores.base import BaseJobStore, ConflictingIdError, JobLookupError
from loguru import logger
from redis import Redis


class RedisJobStore(BaseJobStore):
    """
    JobStore que persiste jobs en Redis.

    Características:
    - Persistencia de jobs entre reinicios
    - Operaciones atómicas con Redis
    - Soporte para clustering (múltiples instancias)
    - Serialización con pickle

    Estructura en Redis:
    - Hash: apscheduler:jobs -> {job_id: pickled_job_state}
    - Sorted Set: apscheduler:run_times -> {job_id: next_run_time_timestamp}
    """

    def __init__(
        self,
        redis_client: Redis,
        jobs_key: str = "apscheduler:jobs",
        run_times_key: str = "apscheduler:run_times",
        pickle_protocol: int = pickle.HIGHEST_PROTOCOL,
    ):
        """
        Inicializa RedisJobStore.

        Args:
            redis_client: Cliente Redis (sync)
            jobs_key: Key para hash de jobs
            run_times_key: Key para sorted set de run times
            pickle_protocol: Protocolo de pickle
        """
        super().__init__()
        self.redis = redis_client
        self.jobs_key = jobs_key
        self.run_times_key = run_times_key
        self.pickle_protocol = pickle_protocol

    def lookup_job(self, job_id: str) -> Optional[Job]:
        """
        Busca un job por ID.

        Args:
            job_id: ID del job

        Returns:
            Job si existe, None si no
        """
        job_state = self.redis.hget(self.jobs_key, job_id)

        if job_state is None:
            return None

        return self._reconstitute_job(job_state)

    def get_due_jobs(self, now: datetime) -> List[Job]:
        """
        Obtiene jobs que deben ejecutarse ahora.

        Args:
            now: Timestamp actual

        Returns:
            Lista de jobs pendientes
        """
        timestamp = now.timestamp()

        # Obtener job_ids con next_run_time <= now
        job_ids = self.redis.zrangebyscore(self.run_times_key, 0, timestamp)

        if not job_ids:
            return []

        # Obtener jobs desde hash
        jobs = []
        for job_id in job_ids:
            job_state = self.redis.hget(self.jobs_key, job_id)
            if job_state:
                try:
                    job = self._reconstitute_job(job_state)
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"Error reconstituyendo job {job_id}", error=str(e))

        return jobs

    def get_next_run_time(self) -> Optional[datetime]:
        """
        Obtiene el próximo tiempo de ejecución.

        Returns:
            Datetime del próximo job o None
        """
        # Obtener el primer elemento del sorted set (menor timestamp)
        result = self.redis.zrange(self.run_times_key, 0, 0, withscores=True)

        if not result:
            return None

        _, timestamp = result[0]
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)

    def get_all_jobs(self) -> List[Job]:
        """
        Obtiene todos los jobs.

        Returns:
            Lista de todos los jobs
        """
        job_states = self.redis.hgetall(self.jobs_key)

        jobs = []
        for job_id, job_state in job_states.items():
            try:
                job = self._reconstitute_job(job_state)
                jobs.append(job)
            except Exception as e:
                logger.error(f"Error reconstituyendo job {job_id}", error=str(e))

        return jobs

    def add_job(self, job: Job) -> None:
        """
        Agrega un job.

        Args:
            job: Job a agregar

        Raises:
            ConflictingIdError: Si el job ya existe
        """
        # Verificar que no exista
        if self.redis.hexists(self.jobs_key, job.id):
            raise ConflictingIdError(job.id)

        # Serializar job
        job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)

        # Pipeline para operaciones atómicas
        pipe = self.redis.pipeline()

        # Guardar job state
        pipe.hset(self.jobs_key, job.id, job_state)

        # Guardar next_run_time si existe
        if job.next_run_time:
            pipe.zadd(self.run_times_key, {job.id: job.next_run_time.timestamp()})

        pipe.execute()

    def update_job(self, job: Job) -> None:
        """
        Actualiza un job existente.

        Args:
            job: Job a actualizar

        Raises:
            JobLookupError: Si el job no existe
        """
        # Verificar que exista
        if not self.redis.hexists(self.jobs_key, job.id):
            raise JobLookupError(job.id)

        # Serializar job
        job_state = pickle.dumps(job.__getstate__(), self.pickle_protocol)

        # Pipeline para operaciones atómicas
        pipe = self.redis.pipeline()

        # Actualizar job state
        pipe.hset(self.jobs_key, job.id, job_state)

        # Actualizar next_run_time
        if job.next_run_time:
            pipe.zadd(self.run_times_key, {job.id: job.next_run_time.timestamp()})
        else:
            # Remover de run_times si no tiene next_run_time
            pipe.zrem(self.run_times_key, job.id)

        pipe.execute()

    def remove_job(self, job_id: str) -> None:
        """
        Elimina un job.

        Args:
            job_id: ID del job a eliminar

        Raises:
            JobLookupError: Si el job no existe
        """
        # Pipeline para operaciones atómicas
        pipe = self.redis.pipeline()

        # Eliminar job state
        pipe.hdel(self.jobs_key, job_id)

        # Eliminar de run_times
        pipe.zrem(self.run_times_key, job_id)

        results = pipe.execute()

        # Verificar que se eliminó algo
        if results[0] == 0:
            raise JobLookupError(job_id)

    def remove_all_jobs(self) -> None:
        """Elimina todos los jobs."""
        pipe = self.redis.pipeline()
        pipe.delete(self.jobs_key)
        pipe.delete(self.run_times_key)
        pipe.execute()

    def shutdown(self) -> None:
        """Cierra el jobstore (no hace nada, Redis se cierra externamente)."""
        pass

    def _reconstitute_job(self, job_state: bytes) -> Job:
        """
        Reconstruye un Job desde su estado serializado.

        Args:
            job_state: Estado del job serializado con pickle

        Returns:
            Job reconstruido
        """
        job_state_dict = pickle.loads(job_state)
        job = Job.__new__(Job)
        job.__setstate__(job_state_dict)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job
