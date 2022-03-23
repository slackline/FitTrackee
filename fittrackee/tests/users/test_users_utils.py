from unittest.mock import patch

import pytest
from flask import Flask

from fittrackee.tests.utils import random_string
from fittrackee.users.exceptions import UserNotFoundException
from fittrackee.users.models import User
from fittrackee.users.utils.admin import set_admin_rights
from fittrackee.users.utils.controls import (
    check_password,
    check_username,
    is_valid_email,
    register_controls,
)


class TestSetAdminRights:
    def test_it_raises_exception_if_user_does_not_exist(
        self, app: Flask
    ) -> None:
        with pytest.raises(UserNotFoundException):
            set_admin_rights(random_string())

    def test_it_sets_admin_right_for_a_given_user(
        self, app: Flask, user_1: User
    ) -> None:
        set_admin_rights(user_1.username)

        assert user_1.admin is True

    def test_it_does_not_raise_exception_when_user_has_already_admin_right(
        self, app: Flask, user_1_admin: User
    ) -> None:
        set_admin_rights(user_1_admin.username)

        assert user_1_admin.admin is True

    def test_it_activates_account_if_user_is_inactive(
        self, app: Flask, inactive_user: User
    ) -> None:
        set_admin_rights(inactive_user.username)

        assert inactive_user.admin is True
        assert inactive_user.is_active is True
        assert inactive_user.confirmation_token is None


class TestIsValidEmail:
    @pytest.mark.parametrize(
        ('input_email',),
        [
            (None,),
            ('',),
            ('foo',),
            ('foo@',),
            ('@foo.fr',),
            ('foo@foo',),
            ('.',),
            ('./',),
        ],
    )
    def test_it_returns_false_if_email_is_invalid(
        self, input_email: str
    ) -> None:
        assert is_valid_email(input_email) is False

    @pytest.mark.parametrize(
        ('input_email',),
        [
            ('admin@example.com',),
            ('admin@test.example.com',),
            ('admin.site@test.example.com',),
            ('admin-site@test-example.com',),
        ],
    )
    def test_it_returns_true_if_email_is_valid(self, input_email: str) -> None:
        assert is_valid_email(input_email) is True


class TestCheckPasswords:
    @pytest.mark.parametrize(
        ('input_password_length',),
        [
            (0,),
            (3,),
            (7,),
        ],
    )
    def test_it_returns_error_message_string_if_password_length_is_below_8_characters(  # noqa
        self, input_password_length: int
    ) -> None:
        password = random_string(input_password_length)
        assert check_password(password) == (
            'password: 8 characters required\n'
        )

    @pytest.mark.parametrize(
        ('input_password_length',),
        [
            (8,),
            (10,),
        ],
    )
    def test_it_returns_empty_string_when_password_length_exceeds_7_characters(
        self, input_password_length: int
    ) -> None:
        password = random_string(input_password_length)
        assert check_password(password) == ''


class TestIsUsernameValid:
    @pytest.mark.parametrize(
        ('input_username_length',),
        [
            (2,),
            (31,),
        ],
    )
    def test_it_returns_error_message_when_username_length_is_invalid(
        self, input_username_length: int
    ) -> None:
        assert (
            check_username(
                username=random_string(31),
            )
            == 'username: 3 to 30 characters required\n'
        )

    @pytest.mark.parametrize(
        ('input_invalid_character',),
        [
            ('.',),
            ('/',),
            ('$',),
        ],
    )
    def test_it_returns_error_message_when_username_has_invalid_character(
        self, input_invalid_character: str
    ) -> None:
        username = random_string() + input_invalid_character
        assert check_username(username=username) == (
            'username: only alphanumeric characters and the '
            'underscore character "_" allowed\n'
        )

    def test_it_returns_empty_string_when_username_is_valid(self) -> None:
        assert check_username(username=random_string()) == ''

    def test_it_returns_multiple_errors(self) -> None:
        username = random_string(31) + '.'
        assert check_username(username=username) == (
            'username: 3 to 30 characters required\n'
            'username: only alphanumeric characters and the underscore '
            'character "_" allowed\n'
        )


class TestRegisterControls:
    module_path = 'fittrackee.users.utils.controls.'
    valid_username = random_string()
    valid_email = f'{random_string()}@example.com'
    valid_password = random_string()

    def test_it_calls_all_validators(self) -> None:
        with patch(
            self.module_path + 'check_password'
        ) as check_passwords_mock, patch(
            self.module_path + 'check_username'
        ) as check_username_mock, patch(
            self.module_path + 'is_valid_email'
        ) as is_valid_email_mock:
            register_controls(
                self.valid_username,
                self.valid_email,
                self.valid_password,
            )

        check_passwords_mock.assert_called_once_with(self.valid_password)
        check_username_mock.assert_called_once_with(self.valid_username)
        is_valid_email_mock.assert_called_once_with(self.valid_email)

    def test_it_returns_empty_string_when_inputs_are_valid(self) -> None:
        assert (
            register_controls(
                self.valid_username,
                self.valid_email,
                self.valid_password,
            )
            == ''
        )

    def test_it_returns_multiple_errors_when_inputs_are_invalid(self) -> None:
        invalid_username = random_string(31)
        assert register_controls(
            username=invalid_username,
            email=invalid_username,
            password=random_string(8),
        ) == (
            'username: 3 to 30 characters required\n'
            'email: valid email must be provided\n'
        )
