import argparse
from enum import auto
import logging

import boto3


def get_auto_scaling_group_name(client, instance_id: str) -> str:
    """Get an autoscaling group name from instance ID"""
    response = client.describe_auto_scaling_instances(InstanceIds=[instance_id])
    return response["AutoScalingInstances"][0]["AutoScalingGroupName"]


def get_target_group_arns(client, autoscaling_group_name: str) -> list[str]:
    """Get the target group ARNs for an ASG"""
    response = client.describe_load_balancer_target_groups(
        AutoScalingGroupName=autoscaling_group_name,
    )
    return [
        asg["LoadBalancerTargetGroupARN"]
        for asg in response["LoadBalancerTargetGroups"]
    ]


def wait_until_in_service(client, instance_id: str, target_group_arn: str):
    """Wait until an instance is in service"""
    waiter = client.get_waiter("target_in_service")
    waiter.wait(
        TargetGroupArn=target_group_arn,
        Targets=[
            {"Id": instance_id},
        ],
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "instance_id",
        type=str,
        help="The ID of the instance",
    )

    return parser.parse_args()


def main(args: argparse.Namespace):
    """The main CLI entrypoint"""
    logging.basicConfig(
        datefmt="%Y-%m-%d %H:%M",
        format="[%(asctime)s] %(levelname)-2s: %(message)s",
        level=logging.INFO,
    )

    logger = logging.getLogger()

    logger.info(f"Waiting until instance {args.instance_id} is healthy in it's ELBs")

    autoscaling_client = boto3.client("autoscaling")
    elbv2_client = boto3.client("elbv2")

    asg_name = get_auto_scaling_group_name(autoscaling_client, args.instance_id)
    logger.info(f"Found ASG: {asg_name}")

    target_group_arns = get_target_group_arns(autoscaling_client, asg_name)
    logger.info(f"ASG configures {len(target_group_arns)} target groups")

    for target_group_arn in target_group_arns:
        target_group_name = target_group_arn.split("/", 1)[1]
        logger.info(f"Waiting for instance to register healthy in {target_group_name}")
        wait_until_in_service(elbv2_client, args.instance_id, target_group_arn)

    logger.info("Instance showing as healthy in all TG's")


if __name__ == "__main__":
    main(parse_args())
