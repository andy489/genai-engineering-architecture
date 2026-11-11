"""Section 14: architecture walkthrough with implementation pseudocode.

PLEASE NOTE THAT: This is valid Python syntax, but `services` represents unimplemented
production integrations. This is not a FastAPI app or a working security gateway.
No dependencies, credentials, network calls, or real charges are required.

These below are architectural controls to Python-style pseudocode so we
can see how to implement the request flow without focusing on framework setup.

                         REQUEST
                            |
                  Verify caller identity --------> 401
                            |
                  Check role + attributes -------> 403
                            |
                  Inspect abuse signals ---------> deny / review
                            |
                  Admit rate + concurrency ------> 429
                            |
                  Reserve spending allowance ----> budget denial
                            |
                  Execute within explicit limits
                            |
                  Reconcile usage + audit outcome
                            |
                  Release concurrency capacity

Every denial stops that request. No model call happens before admission.
Cleanup and accounting also apply to provider errors and client cancellation.
"""

async def protected_chat(request, services):
    # BLOCK 1 -- AUTHENTICATE AND AUTHORIZE
    # Raises 401 for missing/invalid credentials. Verify signature, allowed
    # algorithm, issuer, audience and expiry; never trust a prompt's role claim.
    caller = services.identity.verify(request.authorization)
    policy = services.policy.for_tenant(caller.tenant_id)

    # RBAC: permitted model/tools. ABAC: tenant ownership, data classification,
    # caller/resource attributes and context. Raises 403; default is deny.
    policy.require_access(caller, request.model, request.resource_ids)
    services.abuse.require_admission(caller)  # May deny or require review.

    # BLOCK 2 -- LIMIT USAGE AND RESERVE BUDGET
    # Validate sizes and model-specific limits; count the complete assembled
    # model input (including retrieved context), not just the user's message.
    prepared = services.inputs.prepare_and_validate(request, caller, policy)
    limits = policy.execution_limits()  # Output tokens, timeout, agent/tool steps.
    allowance = services.cost.maximum_charge(prepared, request.model, limits)

    # Shared, atomic admission across replicas: caller AND tenant limits.
    # Raises 429 (with appropriate retry guidance) when capacity is unavailable.
    # A lease handles crashes; renew while work runs and release on every exit.
    async with services.limiter.admit(caller, policy) as capacity_lease:
        # Atomic reserve against shared budgets before chargeable work starts.
        # Denial exits this context and releases the concurrency lease.
        reservation = services.budget.reserve(caller, allowance)
        outcome, receipt = "failed_or_cancelled", None
        try:
            # BLOCK 3 -- EXECUTE, ACCOUNT AND OBSERVE
            result = await services.model.generate(
                model=request.model,
                input=prepared,
                limits=limits,
                request_id=reservation.request_id,
            )
            receipt = result.usage_receipt
            outcome = "completed"
            return result.response
        finally:
            # Idempotent, durable accounting keyed by request ID. On success,
            # charge actual usage and release unused allowance. If usage is
            # unknown after failure/cancellation, KEEP the reservation and
            # reconcile later. A failed call is not necessarily a free call.
            try:
                services.budget.settle_or_queue(reservation, receipt)
            finally:
                services.telemetry.record_and_evaluate(
                    subject=caller.audit_token,
                    tenant=caller.tenant_id,
                    model=request.model,
                    request_id=reservation.request_id,
                    outcome=outcome,
                    usage=receipt,
                )  # Metadata only: no credentials, raw prompts or responses.
    # The limiter context releases concurrency even if accounting/audit fails.


# PRODUCTION CONTRACTS (explain briefly; these are not implemented here):
# - Each rejecting service also emits minimal denial metadata. Correlate repeated
#   denials, traffic bursts and spend spikes; one failure is not proof of abuse.
# - Durable admission/accounting must survive worker crashes and cancellation.
#   Unknown charges keep their allowance reserved; a recovery worker reconciles.
# - Every agent tool call needs its own scoped authorization and argument checks.
#   Sensitive actions require approval bound to the specific action and target.
# - Retries consume limits and budget too. Enforce limits at downstream services.
# - Budget denial uses an explicit API policy; 429 here describes rate/capacity.

if __name__ == "__main__":
    print("Read-through pseudocode only: no services are implemented or invoked.")