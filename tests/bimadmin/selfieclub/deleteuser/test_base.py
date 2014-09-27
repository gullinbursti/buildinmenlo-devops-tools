def test_get_configuration_files():
    from bimadmin.selfieclub import deleteuser
    environment = '9GRPw6nquu'
    file_names = deleteuser.get_configuration_files(environment)
    assert isinstance(file_names, list)
    assert len(file_names) == 2
    for file_name in file_names:
        assert '-{}'.format(environment) in file_name
