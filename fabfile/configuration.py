from fabric.api import *
from fabric.contrib.files import upload_template
from jinja2 import Environment, FileSystemLoader

cfg = None


@task
def setup_env(cfg="etc/ep.docker-local.cfg"):
    """

    :param cfg:
    :return:
    """
    import configparser

    CONFIG_FILE = cfg
    config = configparser.ConfigParser()

    config.read(CONFIG_FILE)

    env.update(config._sections['energyportal'])
    env.update(config._sections['ec2'])
    env.update(config._sections['ep_common'])
    env.update(config._sections['db'])
    env.update(config._sections['influxdb'])
    env.update(config._sections['secure_server'])
    env.update(config._sections['prefect'])
    env.update(config._sections['messaging'])

    env.update({'setup_env_has_run': True})

    return config


@task
def configure_docker_env():
    assert env.setup_env_has_run

    create_file_from_template(template_name='docker-env_template', target_file="etc/docker-env")


def create_file_from_template(template_name, target_file, template_directory='fabfile/templates'):
    tmpl_env = Environment(loader=FileSystemLoader(template_directory))
    template = tmpl_env.get_template(template_name)
    output_from_parsed_template = template.render(env)
    with open(target_file, "w") as fh:
        fh.write(output_from_parsed_template)


@task
def configure_local_settings():
    assert env.setup_env_has_run

    import random
    env.secret_key = ''.join(
        [random.SystemRandom().choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])

    create_file_from_template(template_name='local_settings_template.py', target_file="local_settings.py")


@task
def configure_remote_hostname_override(target='prod'):
    """
    @todo testing
    Write django settings override files to <project>/settings/components/env for remote deployment.

    This reads from 'etc/ep.remote.cfg' template parameters for 'remote.template.py'.

    The target parameter is used to chose from 'energyportal_<target>' config sections in 'ep.remote.cfg'.

    :param target: one of 'prod' or 'staging'
    :return: writes file /home/ubuntu/ep_site/settings/components/env/<target>.py
    """
    config = setup_env('etc/ep.remote.cfg')
    env.update(config._sections['energyportal_%s' % target])

    upload_template('remote.template.py',
                    '/home/ubuntu/ep_site/settings/components/env/%s.py' % target,
                    use_sudo=True, template_dir='fabfile/templates', use_jinja=True, context=env)
