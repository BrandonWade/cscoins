from .BaseCommand import BaseCommand
from caserver.challenges import Submission


class SubmissionCommand(BaseCommand):
    def __init__(self, central_authority_server):
        BaseCommand.__init__(self, central_authority_server, "submission")
        self.database = self.central_authority_server.database

    def execute(self, response, client_connection, args):
        remote_ip = client_connection.get_remote_ip()
        response["type"] = 'submission'
        if not self.central_authority_server.is_ip_allowed_to_submit(remote_ip):
            response["error"] = "This IP Address isn't allowed to do submission"
            print("{0} is not allowed to do submission".format(remote_ip))
            return

        try:
            nonce = int(args['nonce'])
            wallet_id = args['wallet_id']

            wallet = self.database.get_wallet_by_id(wallet_id)

            if wallet is None:
                response["error"] = "Unregistered wallet"
                return

            current_challenge = self.database.get_current_challenge()
            submission = Submission(current_challenge.id, nonce, wallet, remote_ip)

            if self.database.is_client_on_submission_cooldown(wallet.nid):
                response["error"] = "Submission for this wallet on cooldown ! Too much invalid submissions"
                return

            if self.database.is_wallet_disqualified(current_challenge.id, wallet.nid):
                response["error"] = "Wallet disqualified for the current challenge"
                return

            print("Submission accepted for Wallet {0}".format(wallet.id))
            self.database.add_or_update_submission(submission)

        except KeyError as e:
            response["error"] = "Missing argument(s)"
        except Exception as e:
            print("{0} exception : {1}".format(self.__class__, e))