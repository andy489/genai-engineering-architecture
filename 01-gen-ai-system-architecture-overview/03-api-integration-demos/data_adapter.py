"""
GloboAssist — Data Adapter Pattern

The orchestrator depends on the DataAdapter interface.
Swapping CRM backends is a configuration change, not a code change.
"""


class DataAdapter:
    """Base interface for external data sources.
    Each adapter normalizes vendor-specific fields
    into a common internal format."""

    def query(self, resource: str, params: dict) -> list[dict]:
        raise NotImplementedError("Subclasses must implement query()")


class ZendeskAdapter(DataAdapter):
    """Connects to Zendesk CRM / ticketing."""

    def __init__(self, base_url: str, api_token: str):
        self.base_url = base_url
        self.api_token = api_token

    def _call_zendesk_api(self, resource, params):
        # HTTP call to Zendesk REST API
        ...

    def query(self, resource: str, params: dict) -> list[dict]:
        raw = self._call_zendesk_api(resource, params)
        # Normalize Zendesk field names to internal format
        return [
            {
                "id": r["id"],
                "summary": r["subject"],
                "status": r["status"],
                "created_at": r["created_at"],
            }
            for r in raw
        ]


class SalesforceAdapter(DataAdapter):
    """Connects to Salesforce CRM."""

    def __init__(self, instance_url: str, access_token: str):
        self.instance_url = instance_url
        self.access_token = access_token

    def _run_soql_query(self, resource, params):
        # SOQL query via Salesforce REST API
        ...

    def query(self, resource: str, params: dict) -> list[dict]:
        raw = self._run_soql_query(resource, params)
        # Normalize Salesforce field names to the same internal format
        return [
            {
                "id": r["Id"],
                "summary": r["Subject"],
                "status": r["Status"],
                "created_at": r["CreatedDate"],
            }
            for r in raw
        ]


# --- Orchestrator usage -------------------------------------------------
# The orchestrator receives its adapter via dependency injection.
# It never knows (or needs to know) which CRM is behind it.

class Orchestrator:
    def __init__(self, data_adapter: DataAdapter):
        self.data_adapter = data_adapter

    def get_ticket_context(self, ticket_id: str) -> list[dict]:
        return self.data_adapter.query(
            resource="tickets",
            params={"id": ticket_id},
        )
