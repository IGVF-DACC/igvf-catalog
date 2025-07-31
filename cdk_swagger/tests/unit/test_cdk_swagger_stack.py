import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_swagger.cdk_swagger_stack import CdkSwaggerStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_swagger/cdk_swagger_stack.py


def test_sqs_queue_created():
    app = core.App()
    stack = CdkSwaggerStack(app, 'cdk-swagger')
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
