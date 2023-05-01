import os

from setuptools import setup

VERSION = "0.1.0"
NAME = "reddit-to-sqlite"
UNDERSCORE_NAME = NAME.replace("-", "_")


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name=NAME,
    description="Create a SQLite database containing data pulled from Reddit",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="David Brownman",
    url=f"https://github.com/xavdid/{NAME}",
    license="MIT",
    version=VERSION,
    packages=[UNDERSCORE_NAME],
    entry_points=f"""
        [console_scripts]
        {NAME}={UNDERSCORE_NAME}.cli:cli
    """,
    install_requires=["sqlite-utils", "click", "requests", "tqdm"],
    extras_require={"test": ["pytest", "requests-mock"]},
    tests_require=[f"{NAME}[test]"],
)
