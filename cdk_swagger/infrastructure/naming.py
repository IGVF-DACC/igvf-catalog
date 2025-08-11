from infrastructure.config import Common


def prepend_project_name(name: str) -> str:
    common = Common()
    return f'{common.project_name}-{name}'


def prepend_branch_name(branch: str, name: str) -> str:
    return f'{branch}-{name}'
