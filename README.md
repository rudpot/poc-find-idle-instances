# Proof of concept code to find and stop idle instances

The POC consists of 

* a lambda function that identifies "idle" instances
* an SNS topic to notify about idle instances
* a lambda function that can be subscribed to the SNS topic and stop idle instances

## Deploying the POC

* Ensure you have the [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-cli-install.html) installed and configured. For easier building it's best to also have docker installed.

* Clone this git repository

* Deploy the resources using the SAM CLI:

    ```bash
    cd find-idle
    sam build --use-container
    sam deploy --guided
    ```

## Tag instances that can be stopped

We want to make sure you only stop resources that are safe to stop. We solve this by requiring a tag named `AutoStop` on the instance. We also recognize that "idle" may mean different things for different instances so we make the `AutoStop` tag do double duty to define an average CPU utilization below which the instance is considered idle. If you don't put a value into the tag, we will assume 10% or lower utilization is "idle".

* Pick one or more instances on which you want to test "idle" detection and tag them with `AutoStop` and a percentage value for your idle threshold

* Navigate to the AWS console, find the cloudformation stack you created with SAM, and from there find the `FindIdleFunction` Lambda function.

* Navigate to the AWS Lambda console for the `FindIdleFunction` and create a test - the function takes no parameters so any test will do. 

* Manually run a "test" on the function. You should now see a list of instances with an 8h average utilization below the threshold in the `AutoStop` tag(s).

## Get notified about instances that can be stopped

We created an SNS topic `FindIdleSnsTopic` and the Lambda `FindIdleFunction` will drop a message on this topic when it detects "idle" instances.

* Navigate to the AWS console, find the cloudformation stack you created with SAM, and from there find the `FindIdleSnsTopic` SNS topic.

* Navigate to the Amazon SNS console for the `FindIdleSnsTopic` and create an "email" subscription. 

* Wait for the subscription confirmation email to arrive and confirm your subscription

* Run the `FindIdleFunction` Lambda again - you should now receive a notification email about any "idle" instances that were detected.

## Enable automatic stopping

We created a `StopIdleFunction` Lambda function for you. This function expects an SNS message with a JSON string representing a list of instances to be stopped.

* Navigate to the AWS console, find the cloudformation stack you created with SAM, and from there find the `StopIdleFunction` Lambda function. Note the ARN of this function.

* Navigate to the Amazon SNS console for the `FindIdleSnsTopic` and create an "lambda" subscription. Use the Lambda ARN from the previous step as a target.

* Navigate to the AWS Lambda console for the `FindIdleFunction` and run another "test".  

You should now receive an email with a list of instances that are deemed "idle" and you should also see that these instances have been "Stopped".

## A note on security

Since we don't know what instances might be found "idle" we need to give our `StopIdleFunction` Lambda function permission to stop any EC2 instance, i.e. the `Resource` section of the [IAM role](https://github.com/rudpot/poc-find-idle-instances/blob/main/find-idle/template.yaml#L111-L122) contains `*`. Since we want to make sure we give our Lambda function the narrowest set of permissions, we have constrained the IAM role to require the presence of the `AutoStop` tag as a constraint to the `*` resource. That way the instance tag now performs three functions:

* Tag an instance as eligible for stopping
* Define a utilization target
* Explicitly limit the Lambda's permission to stop instances

## Next steps

This is a proof of concept only. Things left to do:

* Improve the utilization heuristic - currently it uses an [average utilization](https://github.com/rudpot/poc-find-idle-instances/blob/main/find-idle/find_idle/app.py#L77-L82) over all the 5min datapoints (normal resolution) over an [8h period](https://github.com/rudpot/poc-find-idle-instances/blob/main/find-idle/find_idle/app.py#L72). You may wish to change the window over which to reason as well as using a "maximum" heuristic rather than an "average"

* Automate the `FindIdleFunction` Lambda execution to [run on a timer](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-create-rule-schedule.html). 

