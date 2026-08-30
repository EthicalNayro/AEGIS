from extras.plugins import PluginConfig


class AEGISReviewConfig(PluginConfig):
    name = "aegis_review"

    verbose_name = "AEGIS Security"

    description = (
        "Human-in-the-loop review interface "
        "for AEGIS AI security findings."
    )

    version = "1.1.0"

    author = "AEGIS Project"

    base_url = "aegis"

    min_version = "2.5.1"
    max_version = "2.5.1"

    default_settings = {
        "aws_region": "us-east-1",
        "findings_table": "aegis-eks-dev-security-findings"
    }


config = AEGISReviewConfig
