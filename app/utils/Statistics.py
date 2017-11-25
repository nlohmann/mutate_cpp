# coding=utf-8

from app.models import Patch, Run
from sqlalchemy.sql import func, and_
import datetime


class Statistics:
    @staticmethod
    def run_stats(project_id=None):
        patch_states = ['incomplete', 'killed', 'survived']
        confirmation_states = ['confirmed', 'ignored', 'unknown']
        run_commands = ['build_command', 'quickcheck_command', 'test_command']
        run_logs = ['success', 'failure', 'timeout', 'nochange']

        # structure of the result dictionary
        result = {
            'patch': {
                'count': {
                    patch_state: 0 for patch_state in patch_states + confirmation_states + ['_all_']
                }
            },
            'run': {
                'count': {
                    command: {
                        log: None for log in run_logs + ['_all_']
                    } for command in run_commands + ['_all_']
                },
                'runtime': {
                    aggregate: {
                        command: {
                            log: None for log in run_logs + ['_all_']
                        } for command in run_commands + ['_all_']
                    } for aggregate in ['sum', 'avg']
                }
            },
            'eta': None
        }

        #############################################################################################
        patch_base_query = Patch.query

        if project_id is not None:
            patch_base_query = patch_base_query.filter(Patch.project_id == project_id)

        for patch_state in patch_states:
            q = patch_base_query.filter(Patch.state == patch_state)
            result['patch']['count'][patch_state] = q.count()
        result['patch']['count']['_all_'] = patch_base_query.count()

        for confirmation_state in confirmation_states:
            q = patch_base_query.filter(and_(Patch.state == 'survived', Patch.confirmation == confirmation_state))
            result['patch']['count'][confirmation_state] = q.count()

        #############################################################################################
        run_base_query = Run.query

        if project_id is not None:
            run_base_query = run_base_query.filter(Run.project_id == project_id)

        for run_command in run_commands:
            for run_log in run_logs:
                q = run_base_query.filter(Run.command == run_command).filter(Run.log == run_log)
                result['run']['count'][run_command][run_log] = q.count()
                result['run']['runtime']['sum'][run_command][run_log] = q.with_entities(func.sum(Run.duration)).scalar() or 0
                result['run']['runtime']['avg'][run_command][run_log] = q.with_entities(func.avg(Run.duration)).scalar() or 0

            q = run_base_query.filter(Run.command == run_command)
            result['run']['count'][run_command]['_all_'] = q.count()
            result['run']['runtime']['sum'][run_command]['_all_'] = q.with_entities(func.sum(Run.duration)).scalar() or 0
            result['run']['runtime']['avg'][run_command]['_all_'] = q.with_entities(func.avg(Run.duration)).scalar() or 0

        for run_log in run_logs:
            q = run_base_query.filter(Run.log == run_log)
            result['run']['count']['_all_'][run_log] = q.count()
            result['run']['runtime']['sum']['_all_'][run_log] = q.with_entities(func.sum(Run.duration)).scalar() or 0
            result['run']['runtime']['avg']['_all_'][run_log] = q.with_entities(func.avg(Run.duration)).scalar() or 0

        result['run']['count']['_all_']['_all_'] = run_base_query.count()
        result['run']['runtime']['sum']['_all_']['_all_'] = run_base_query.with_entities(func.sum(Run.duration)).scalar() or 0
        result['run']['runtime']['avg']['_all_']['_all_'] = run_base_query.with_entities(func.avg(Run.duration)).scalar() or 0

        #############################################################################################

        result['eta'] = datetime.datetime.now() + datetime.timedelta(seconds=result['patch']['count']['incomplete'] * result['run']['runtime']['avg']['_all_']['_all_'])

        return result
