"""测试套件全局配置。"""

from hypothesis import HealthCheck, settings


settings.register_profile(
    "ci",
    settings(
        max_examples=120,
        derandomize=True,
        deadline=None,
        print_blob=True,
        suppress_health_check=[HealthCheck.too_slow],
    ),
)
settings.load_profile("ci")
