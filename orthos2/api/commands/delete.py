import json
import logging

from django.conf.urls import url
from django.contrib.auth.models import AnonymousUser, User
from django.http import JsonResponse
from django.shortcuts import redirect, reverse

from api.commands import BaseAPIView, get_machine
from api.forms import (DeleteMachineAPIForm, DeleteRemotePowerAPIForm,
                       DeleteSerialConsoleAPIForm)
from api.serializers.misc import (AuthRequiredSerializer, ErrorMessage,
                                  InputSerializer, Message)
from data.models import Machine
from utils.misc import format_cli_form_errors

logger = logging.getLogger('api')


class Delete:
    MACHINE = 'machine'
    SERIALCONSOLE = 'serialconsole'
    REMOTEPOWER = 'remotepower'

    as_list = [MACHINE, SERIALCONSOLE, REMOTEPOWER]


class DeleteCommand(BaseAPIView):

    METHOD = 'GET'
    URL = '/delete'
    ARGUMENTS = (
        ['args*'],
    )

    HELP_SHORT = "Removes information from the database."
    HELP = """Deletes items from the database.

Usage:
    DELETE <item> [args*]

Arguments:
    item - Specify the item which should be deleted. Items are:

             machine       : Delete a machine (superusers only).
             serialconsole : Delete serial console of a specifc machine
                             (superusers only).
             remotepower   : Delete remote power of a specifc machine
                             (superusers only).

Example:
    DELETE machine
"""

    @staticmethod
    def get_urls():
        return [
            url(r'^delete$', DeleteCommand.as_view(), name='delete'),
        ]

    @staticmethod
    def get_tabcompletion():
        return Delete.as_list

    def get(self, request, *args, **kwargs):
        """
        Dispatcher for the 'delete' command.
        """
        arguments = request.GET.get('args', None)

        if arguments:
            arguments = arguments.split()
            item = arguments[0].lower()
            sub_arguments = arguments[1:]
        else:
            return ErrorMessage("Item is missing!").as_json

        if item == Delete.MACHINE:
            if len(sub_arguments) != 0:
                return ErrorMessage("Invalid number of arguments for 'machine'!").as_json

            return redirect(reverse('api:machine_delete'))

        elif item == Delete.SERIALCONSOLE:
            if len(sub_arguments) != 0:
                return ErrorMessage("Invalid number of arguments for 'serialconsole'!").as_json

            return redirect(reverse('api:serialconsole_delete'))

        elif item == Delete.REMOTEPOWER:
            if len(sub_arguments) != 0:
                return ErrorMessage("Invalid number of arguments for 'remotepower'!").as_json

            return redirect(reverse('api:remotepower_delete'))

        return ErrorMessage("Unknown item '{}'!".format(item)).as_json


class DeleteMachineCommand(BaseAPIView):

    URL_POST = '/machine/delete'

    @staticmethod
    def get_urls():
        return [
            url(r'^machine/delete', DeleteMachineCommand.as_view(), name='machine_delete'),
        ]

    def get(self, request, *args, **kwargs):
        """
        Return form for deleting a machine.
        """
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        form = DeleteMachineAPIForm()

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST,
            form.get_order()
        )
        return input.as_json

    def post(self, request, *args, **kwargs):
        """
        Delete machine.
        """
        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = DeleteMachineAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                machine = Machine.objects.get(fqdn__iexact=cleaned_data['fqdn'])

                if machine.is_virtual_machine():
                    host = machine.get_hypervisor()

                    if host.virtualization_api is None:
                        return ErrorMessage("No virtualization API found!").as_json

                    if host.virtualization_api.remove(machine):
                        result = machine.delete()
                else:
                    result = machine.delete()

                theader = [
                    {'objects': 'Deleted objects'},
                    {'count': '#'},
                ]

                response = {
                    'header': {'type': 'TABLE', 'theader': theader},
                    'data': [],
                }
                for key, value in result[1].items():
                    response['data'].append(
                        {
                            'objects': key.replace('data.', ''),
                            'count': value
                        }
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteSerialConsoleCommand(BaseAPIView):

    URL_POST = '/serialconsole/delete'

    @staticmethod
    def get_urls():
        return [
            url(
                r'^serialconsole/delete',
                DeleteSerialConsoleCommand.as_view(),
                name='serialconsole_delete'
            ),
        ]

    def get(self, request, *args, **kwargs):
        """
        Return form for deleting a serial console.
        """
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        form = DeleteSerialConsoleAPIForm()

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST,
            form.get_order()
        )
        return input.as_json

    def post(self, request, *args, **kwargs):
        """
        Delete serial console.
        """
        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = DeleteSerialConsoleAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                machine = Machine.objects.get(fqdn__iexact=cleaned_data['fqdn'])

                if not machine.has_serialconsole():
                    return ErrorMessage("Machine has no serial console!").as_json

                result = machine.serialconsole.delete()

                theader = [
                    {'objects': 'Deleted objects'},
                    {'count': '#'},
                ]

                response = {
                    'header': {'type': 'TABLE', 'theader': theader},
                    'data': [],
                }
                for key, value in result[1].items():
                    response['data'].append(
                        {
                            'objects': key.replace('data.', ''),
                            'count': value
                        }
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json


class DeleteRemotePowerCommand(BaseAPIView):

    URL_POST = '/remotepower/delete'

    @staticmethod
    def get_urls():
        return [
            url(
                r'^remotepower/delete',
                DeleteRemotePowerCommand.as_view(),
                name='remotepower_delete'
            ),
        ]

    def get(self, request, *args, **kwargs):
        """
        Return form for deleting a remote power.
        """
        if isinstance(request.user, AnonymousUser) or not request.auth:
            return AuthRequiredSerializer().as_json

        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        form = DeleteRemotePowerAPIForm()

        input = InputSerializer(
            form.as_dict(),
            self.URL_POST,
            form.get_order()
        )
        return input.as_json

    def post(self, request, *args, **kwargs):
        """
        Delete remote power.
        """
        if not request.user.is_superuser:
            return ErrorMessage("Only superusers are allowed to perform this action!").as_json

        data = json.loads(request.body.decode('utf-8'))['form']
        form = DeleteRemotePowerAPIForm(data)

        if form.is_valid():

            try:
                cleaned_data = form.cleaned_data

                machine = Machine.objects.get(fqdn__iexact=cleaned_data['fqdn'])

                if not machine.has_remotepower():
                    return ErrorMessage("Machine has no remote power!").as_json

                result = machine.remotepower.delete()

                theader = [
                    {'objects': 'Deleted objects'},
                    {'count': '#'},
                ]

                response = {
                    'header': {'type': 'TABLE', 'theader': theader},
                    'data': [],
                }
                for key, value in result[1].items():
                    response['data'].append(
                        {
                            'objects': key.replace('data.', ''),
                            'count': value
                        }
                    )
                return JsonResponse(response)

            except Exception as e:
                logger.exception(e)
                return ErrorMessage("Something went wrong!").as_json

        return ErrorMessage("\n{}".format(format_cli_form_errors(form))).as_json
