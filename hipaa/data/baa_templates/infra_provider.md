# Outreach: {vendor_name} BAA Request (Infrastructure)

**Subject:** BAA and infrastructure safeguards review for {requester_org}

{vendor_name} team,

{requester_org} runs production workloads on {vendor_name} for {service_description}, and those workloads process or persist protected health information. Specifically, our footprint covers: {ephi_scope}.

Because {vendor_name} sits at the infrastructure layer, the technical safeguards under 45 CFR §164.312(a) and §164.312(e) apply directly to your platform, not just our application code. Before we can certify our HIPAA posture, we need a signed Business Associate Agreement plus documented assurances on the items below.

Encryption and key management:

1. Encryption at rest across compute, object storage, block storage, and managed databases (algorithm, key length, KMS or HSM model).
2. Encryption in transit for control plane, data plane, and inter-service traffic, including TLS versions accepted and any internal mTLS.
3. Customer-managed key (CMK) options if you support them, and rotation cadence.

Logging and retention:

1. Audit log coverage for administrative actions, data access events, and authentication.
2. Retention window (we target 6 years to align with HIPAA documentation retention rules under §164.316).
3. Tamper-evident or write-once log storage options.

Region, residency, and sub-processors:

1. Confirmation that we can pin our workloads to specific geographic regions.
2. The current sub-processor list, including any change notification process (we need at least 30 days notice on additions that touch PHI).
3. Any cross-border data transfer paths we should be aware of.

We'd like to execute the BAA within {target_weeks} weeks and hold a short technical review afterward to walk through the safeguards above. Risk tier on our side: **{risk_tier}**.

Please loop in whoever owns BAA execution and the security or trust team contact who can speak to the technical items.

Thanks,
{requester_name}
{requester_org}
