from aws_cdk import App

from infrastructure.build import build


def synth() -> None:
    app = App()
    build(app)
    app.synth()


if __name__ == '__main__':
    synth()
