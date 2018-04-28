Integration tests
---------------------------

Integration tests are located in `**/tests/integration/**`

In order to run them, you need to install docker. To be able to run docker without root privileges, ensure that your user is in docker group https://docs.docker.com/install/linux/linux-postinstall/

To run tests, execute following command:

`DJANGO_SETTINGS_MODULE=waldur_core.server.test_settings waldur test waldur_ansible --tag=integration`

Alternatively, you can also run them with `pytest`. You also should set `DJANGO_SETTINGS_MODULE` variable and provide `--tag=integration flag`.
