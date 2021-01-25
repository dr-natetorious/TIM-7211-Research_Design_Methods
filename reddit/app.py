#!/usr/bin/env python3
import os.path
from aws_cdk.core import App, Stack, Environment
from infra.exports import create_layers
src_root_dir = os.path.join(os.path.dirname(__file__))

default_env= Environment(region="us-west-2")

app = App()
infra_stack = Stack(app,'WSBScraper', env=default_env)
create_layers(infra_stack)
app.synth()
