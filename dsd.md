Vamos añadir una tarea inicial que consistirá en migrar, consolidar y refactorizar de la siguiente manera los siguientes archivos: 



src/shared/config/ai_processing_config.py es probablemente una redundancia de las configuraciones segregadas src/shared/config/chunking_config.py

src/shared/config/embedding_config.py

src/shared/config/deduplication_config.py

src/shared/config/clustering_config.py

src/shared/config/rag_config.py 



Por ende deberás incluir la migración de la configuración a sus respectivos archivos 



Los siguientes solo será copiarlos tal cual a la nueva estructura pero con el nombre del archivo sin el sufijo config: 



src/shared/config/app_config.py > src/shared/config/app/config.py AppConfig



src/shared/config/chunking_config.py > src/shared/config/app/chunking.py ChunkingConfig



src/shared/config/embedding_config.py debe unificarse en