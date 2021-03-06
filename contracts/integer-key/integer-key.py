# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import shlex
import logging

logger = logging.getLogger(__name__)

from pdo.client.SchemeExpression import SchemeExpression
from pdo.client.controller.commands.send import send_to_contract

## -----------------------------------------------------------------
## -----------------------------------------------------------------
def __command_integer_key__(state, bindings, pargs) :
    """controller command to interact with an integer-key contract
    """

    parser = argparse.ArgumentParser(prog='integer_key')
    parser.add_argument('-e', '--enclave', help='URL of the enclave service to use', type=str)
    parser.add_argument('-f', '--save-file', help='File where contract data is stored', type=str)
    parser.add_argument('-q', '--quiet', help='Suppress printing the result', action='store_true')
    parser.add_argument('-w', '--wait', help='Wait for the transaction to commit', action='store_true')

    subparsers = parser.add_subparsers(dest='command')

    subparser = subparsers.add_parser('get_signing_key')
    subparser.add_argument('-s', '--symbol', help='binding symbol for result', type=str)

    subparser = subparsers.add_parser('create')
    subparser.add_argument('-k', '--key', help='key to create', type=str, required=True)
    subparser.add_argument('-v', '--value', help='initial value to give to the key', type=int, default=0)

    subparser = subparsers.add_parser('inc')
    subparser.add_argument('-k', '--key', help='key to increment', type=str, required=True)
    subparser.add_argument('-v', '--value', help='initial value to give to the key', type=int, required=True)

    subparser = subparsers.add_parser('dec')
    subparser.add_argument('-k', '--key', help='key to decrement', type=str, required=True)
    subparser.add_argument('-v', '--value', help='initial value to give to the key', type=int, required=True)

    subparser = subparsers.add_parser('get')
    subparser.add_argument('-k', '--key', help='key to retrieve', type=str, required=True)

    subparser = subparsers.add_parser('transfer')
    subparser.add_argument('-k', '--key', help='key to transfer', type=str, required=True)
    subparser.add_argument('-o', '--owner', help='identity to transfer ownership', type=str, required=True)

    subparser = subparsers.add_parser('escrow')
    subparser.add_argument('-k', '--key', help='key to escrow', type=str, required=True)
    subparser.add_argument('-a', '--agent', help='identity of the escrow agent', type=str, required=True)

    subparser = subparsers.add_parser('attestation')
    subparser.add_argument('-k', '--key', help='key to escrow', type=str, required=True)
    subparser.add_argument('-s', '--symbol', help='binding symbol for result', type=str)

    subparser = subparsers.add_parser('disburse')
    subparser.add_argument('-a', '--attestation', help='Disburse attestation from the escrow agent', type=str, required=True)

    subparser = subparsers.add_parser('exchange')
    subparser.add_argument('-a', '--attestation', help='Disburse attestation from the escrow agent', type=str, required=True)

    options = parser.parse_args(pargs)

    extraparams={'quiet' : options.quiet, 'wait' : options.wait}

    if options.command == 'get_signing_key' :
        message = "'(get-public-signing-key)"
        result = send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        if result and options.symbol :
            bindings.bind(options.symbol, result)
        return

    if options.command == 'create' :
        message = "'(create \"{0}\" {1})".format(options.key, options.value)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'inc' :
        message = "'(inc \"{0}\" {1})".format(options.key, options.value)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'dec' :
        message = "'(dec \"{0}\" {1})".format(options.key, options.value)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'get' :
        extraparams['commit'] = False
        message = "'(get-value \"{0}\")".format(options.key)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'transfer' :
        message = "'(transfer-ownership \"{0}\" \"{1}\")".format(options.key, options.owner)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'escrow' :
        message = "'(escrow \"{0}\" \"{1}\")".format(options.key, options.agent)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'attestation' :
        message = "'(escrow-attestation \"{0}\")".format(options.key)
        result = send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        if result and options.symbol :
            bindings.bind(options.symbol, result)
        return

    if options.command == 'disburse' :
        attestation = SchemeExpression.ParseExpression(options.attestation)
        assetkey = dict(attestation.nth(0).value)['key']
        dependencies = str(attestation.nth(1))
        signature = str(attestation.nth(2))
        message = "'(disburse \"{0}\" {1} {2})".format(assetkey, dependencies, signature)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

    if options.command == 'exchange' :
        attestation = SchemeExpression.ParseExpression(options.attestation)
        offered = dict(attestation.nth(0).value)['key']
        maxbid = dict(attestation.nth(1).value)['key']
        dependencies = str(attestation.nth(2))
        signature = str(attestation.nth(3))
        message = "'(exchange-ownership \"{0}\" \"{1}\" {2} {3})".format(offered, maxbid, dependencies, signature)
        send_to_contract(state, options.save_file, options.enclave, message, **extraparams)
        return

## -----------------------------------------------------------------
## -----------------------------------------------------------------
def do_integer_key(self, args) :
    """
    integer_key -- invoke integer key commands
    """

    pargs = shlex.split(self.bindings.expand(args))

    try :
        __command_integer_key__(self.state, self.bindings, pargs)

    except SystemExit as se :
        if se.code > 0 : print('An error occurred processing {0}: {1}'.format(args, str(se)))
        return

    except Exception as e :
        print('An error occurred processing {0}: {1}'.format(args, str(e)))
        return

## -----------------------------------------------------------------
## -----------------------------------------------------------------
def load_commands(cmdclass) :
    setattr(cmdclass, 'do_integer_key', do_integer_key)
