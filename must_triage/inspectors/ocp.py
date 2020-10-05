import yaml

import must_triage.fs as fs
import must_triage.inspectors.base as base


class OCP(base.Inspector):
    gather_types = dict(
        yaml=dict(
            match=lambda p: fs.has_ext(p, ['yaml', 'yml']),
            description="Reading OCP YAML files",
        ),
    )

    @staticmethod
    def inspect_yaml(path):
        result = {path: list()}
        with open(path) as fd:
            try:
                obj = yaml.safe_load(fd)
            except (yaml.scanner.ScannerError, yaml.parser.ParserError):
                result[path].append("Failed to parse YAML content")
                return result
        if 'kind' in obj:
            result[path].extend(OCP.operator_success(obj))
            pods = list()
            if obj['kind'].lower() == 'pod':
                pods.append(obj)
            elif obj['kind'].lower() == 'podlist':
                pods.extend(filter(
                    lambda o: o['kind'].lower() == 'pod',
                    obj['items']
                ))
            result[path].extend(map(OCP.pod_ready, pods))
        if 'error' in obj:
            result[path].append(obj)
        return result

    @staticmethod
    def operator_success(obj):
        result = list()
        if obj['kind'] != 'ClusterServiceVersion':
            return result
        status = obj['status']
        if status['phase'].lower() == 'succeeded':
            return result
        result.append(
            f"Operator phase is '{status['phase']}', "
            "not 'Succeeded' as expected"
        )
        return result

    @staticmethod
    def pod_ready(obj):
        result = list()
        status = obj['status']
        try:
            container_statuses = status['containerStatuses']
        except KeyError:
            return [dict(
                pod_name=obj['metadata']['name'],
                status=status,
                )]
        not_ready = filter(lambda cs: cs['ready'] is False, container_statuses)
        for cs in not_ready:
            ts = cs['state'].get('terminated', dict())
            if (ts.get('reason', '').lower() == 'completed' and
                    ts.get('exitCode') == 0):
                continue
            result.append(
                f"Container '{cs['name']}' in "
                f"pod '{obj['metadata']['name']}' is not ready")
        return result
