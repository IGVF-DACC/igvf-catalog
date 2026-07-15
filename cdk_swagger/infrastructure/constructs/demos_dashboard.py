from dataclasses import dataclass

from aws_cdk import Duration
from aws_cdk import aws_apigatewayv2 as apigwv2
from aws_cdk import aws_apigatewayv2_integrations as apigwv2_integrations
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_secretsmanager as secretsmanager

from constructs import Construct


@dataclass
class DemosDashboardProps:
    pass


class DemosDashboard(Construct):
    '''
    Read-only dashboard listing currently active demo stacks (one per branch
    deployed via infrastructure/stacks/pipeline.py's DemoDeploymentPipelineStack),
    when each was last deployed, and the commit hash of its last pipeline
    execution. See lambda/demos_dashboard/handler.py for the actual logic.
    '''

    def __init__(
        self,
        scope: Construct,
        id: str,
        props: DemosDashboardProps,
    ) -> None:
        super().__init__(scope, id)
        self.props = props

        self.credentials_secret = secretsmanager.Secret(
            self,
            'Credentials',
            description='Basic auth credentials for the IGVF Catalog demos dashboard',
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "igvf-demo"}',
                generate_string_key='password',
                exclude_punctuation=True,
                password_length=24,
            ),
        )

        self.function = lambda_.Function(
            self,
            'Function',
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler='handler.handler',
            code=lambda_.Code.from_asset('lambda/demos_dashboard'),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                'CREDENTIALS_SECRET_ARN': self.credentials_secret.secret_arn,
            },
        )
        self.credentials_secret.grant_read(self.function)

        # Read-only introspection permissions. These APIs don't support
        # meaningfully scoped resource ARNs (CloudFormation) or aren't worth
        # scoping further given they're read-only and expose no secrets.
        self.function.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    'cloudformation:DescribeStacks',
                    'cloudformation:DescribeStackResources',
                    'codepipeline:ListPipelineExecutions',
                    'tag:GetResources',
                ],
                resources=['*'],
            )
        )

        self.http_api = apigwv2.HttpApi(
            self,
            'Api',
            default_integration=apigwv2_integrations.HttpLambdaIntegration(
                'DefaultIntegration',
                self.function,
            ),
        )
