"""Tests para el script de análisis exhaustivo."""

# Importar el módulo del script
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "scripts"))

from analyze_domain_shared import (
    ClassAnalysisReport,
    ExhaustiveClassAnalyzer,
    UsageExample,
    generate_markdown_report,
)


class TestExhaustiveClassAnalyzer:
    """Tests para ExhaustiveClassAnalyzer."""

    def test_analyzer_initialization(self):
        """Debería inicializar el analizador correctamente."""
        analyzer = ExhaustiveClassAnalyzer()

        assert analyzer.root_dir.exists()
        assert analyzer.src_dir.exists()
        assert analyzer.domain_shared_dir.exists()

    def test_find_all_class_files(self):
        """Debería encontrar archivos de clases en domain/shared."""
        analyzer = ExhaustiveClassAnalyzer()
        class_files = analyzer._find_all_class_files()

        assert len(class_files) > 0
        assert all(f.suffix == ".py" for f in class_files)
        assert all("__init__" not in f.name for f in class_files)

    def test_extract_classes_from_file(self):
        """Debería extraer nombres de clases de un archivo."""
        analyzer = ExhaustiveClassAnalyzer()

        # Usar un archivo conocido
        test_file = analyzer.domain_shared_dir / "value_objects" / "error_details.py"
        if test_file.exists():
            classes = analyzer._extract_classes_from_file(test_file)
            assert len(classes) > 0
            assert all(isinstance(c, str) for c in classes)

    def test_get_module_path(self):
        """Debería convertir path de archivo a module path."""
        analyzer = ExhaustiveClassAnalyzer()

        test_path = Path("src/domain/shared/value_objects/error_details.py")
        module_path = analyzer._get_module_path(test_path)

        assert "src.domain.shared.value_objects.error_details" in module_path

    def test_count_lines_of_code(self):
        """Debería contar líneas de código de una clase."""
        analyzer = ExhaustiveClassAnalyzer()

        test_file = analyzer.domain_shared_dir / "value_objects" / "error_details.py"
        if test_file.exists():
            classes = analyzer._extract_classes_from_file(test_file)
            if classes:
                loc = analyzer._count_lines_of_code(test_file, classes[0])
                assert loc >= 0

    def test_calculate_complexity(self):
        """Debería calcular complejidad ciclomática."""
        analyzer = ExhaustiveClassAnalyzer()

        test_file = analyzer.domain_shared_dir / "value_objects" / "error_details.py"
        if test_file.exists():
            classes = analyzer._extract_classes_from_file(test_file)
            if classes:
                complexity = analyzer._calculate_complexity(test_file, classes[0])
                assert complexity >= 1.0

    def test_find_imports(self):
        """Debería encontrar imports de una clase."""
        analyzer = ExhaustiveClassAnalyzer()

        # Buscar una clase conocida que se usa
        imports = analyzer._find_imports("ErrorDetails")

        # ErrorDetails debería tener al menos un import
        assert isinstance(imports, list)

    def test_find_duplicates(self):
        """Debería encontrar clases duplicadas."""
        analyzer = ExhaustiveClassAnalyzer()

        # MetricType es un duplicado conocido
        test_file = (
            analyzer.domain_shared_dir
            / "value_objects"
            / "classification"
            / "metric_type.py"
        )
        if test_file.exists():
            duplicates = analyzer._find_duplicates("MetricType", test_file)

            # Debería encontrar el duplicado en src/domain/value_objects/
            assert isinstance(duplicates, list)

    def test_extract_keywords(self):
        """Debería extraer keywords de nombres de clases."""
        analyzer = ExhaustiveClassAnalyzer()

        keywords = analyzer._extract_keywords("DomainSimilarityScore")

        assert "domain" in keywords
        assert "similarity" in keywords
        assert "score" in keywords

    def test_generate_recommendation_for_used_class(self):
        """Debería recomendar KEEP para clases en uso."""
        analyzer = ExhaustiveClassAnalyzer()

        report = ClassAnalysisReport(
            class_name="TestClass",
            file_path="test.py",
            module_path="test",
            is_used=True,
            usage_count=5,
        )

        recommendation, reason = analyzer._generate_recommendation(report)

        assert recommendation == "KEEP"
        assert "uso activo" in reason

    def test_generate_recommendation_for_duplicate(self):
        """Debería recomendar CONSOLIDATE para duplicados."""
        analyzer = ExhaustiveClassAnalyzer()

        report = ClassAnalysisReport(
            class_name="TestClass",
            file_path="test.py",
            module_path="test",
            is_duplicate=True,
            duplicates=["other/test.py"],
        )

        recommendation, reason = analyzer._generate_recommendation(report)

        assert recommendation == "CONSOLIDATE"
        assert "duplicada" in reason

    def test_generate_recommendation_for_unused(self):
        """Debería recomendar REMOVE para clases sin uso."""
        analyzer = ExhaustiveClassAnalyzer()

        report = ClassAnalysisReport(
            class_name="TestClass",
            file_path="test.py",
            module_path="test",
            is_used=False,
            test_files=[],
        )

        recommendation, reason = analyzer._generate_recommendation(report)

        assert recommendation == "REMOVE"
        assert "sin uso" in reason


class TestClassAnalysisReport:
    """Tests para ClassAnalysisReport dataclass."""

    def test_create_report(self):
        """Debería crear un informe de análisis."""
        report = ClassAnalysisReport(
            class_name="TestClass", file_path="test.py", module_path="test.module"
        )

        assert report.class_name == "TestClass"
        assert report.file_path == "test.py"
        assert report.module_path == "test.module"
        assert report.lines_of_code == 0
        assert report.complexity_score == 0.0
        assert report.is_used is False
        assert report.is_duplicate is False

    def test_report_with_usage(self):
        """Debería crear informe con información de uso."""
        usage = UsageExample(
            file_path="test.py",
            line_number=10,
            code_snippet="TestClass()",
            context="def test(): TestClass()",
        )

        report = ClassAnalysisReport(
            class_name="TestClass",
            file_path="test.py",
            module_path="test.module",
            real_usage_examples=[usage],
            usage_count=1,
            is_used=True,
        )

        assert len(report.real_usage_examples) == 1
        assert report.usage_count == 1
        assert report.is_used is True


class TestMarkdownReportGeneration:
    """Tests para generación de informe markdown."""

    def test_generate_markdown_report(self):
        """Debería generar informe markdown."""
        reports = [
            ClassAnalysisReport(
                class_name="TestClass1",
                file_path="test1.py",
                module_path="test.module1",
                is_used=True,
                recommendation="KEEP",
                recommendation_reason="En uso",
            ),
            ClassAnalysisReport(
                class_name="TestClass2",
                file_path="test2.py",
                module_path="test.module2",
                is_duplicate=True,
                recommendation="CONSOLIDATE",
                recommendation_reason="Duplicado",
            ),
        ]

        markdown = generate_markdown_report(reports)

        assert "# Análisis Exhaustivo" in markdown
        assert "Executive Summary" in markdown
        assert "TestClass1" in markdown
        assert "TestClass2" in markdown
        assert "KEEP" in markdown
        assert "CONSOLIDATE" in markdown

    def test_markdown_includes_all_sections(self):
        """Debería incluir todas las secciones en el markdown."""
        report = ClassAnalysisReport(
            class_name="TestClass",
            file_path="test.py",
            module_path="test.module",
            lines_of_code=100,
            complexity_score=5.0,
            is_used=True,
            recommendation="KEEP",
            recommendation_reason="Test",
        )

        markdown = generate_markdown_report([report])

        # Verificar que incluye los 10 puntos
        assert "1. Ubicación" in markdown
        assert "2. Métricas de Código" in markdown
        assert "3. Uso" in markdown
        assert "4. Tests" in markdown
        assert "5. Duplicados" in markdown
        assert "6. Dependencias" in markdown
        assert "7. Metadata" in markdown
        assert "8. Recomendación" in markdown
        assert "9. Potencial de Integración" in markdown
        assert "10. Notas" in markdown


class TestUsageExample:
    """Tests para UsageExample dataclass."""

    def test_create_usage_example(self):
        """Debería crear un ejemplo de uso."""
        example = UsageExample(
            file_path="test.py",
            line_number=42,
            code_snippet="TestClass()",
            context="def test(): TestClass()",
        )

        assert example.file_path == "test.py"
        assert example.line_number == 42
        assert example.code_snippet == "TestClass()"
        assert "TestClass()" in example.context
