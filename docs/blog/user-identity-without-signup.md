# User Identity without signup

You can keep track of people using your MCP product before they create an
account.

ChatGPT sends an anonymized user ID called `openai/subject` with tool calls. You
can use it to count free usage, apply rate limits, and recognize repeat visitors.
OpenAI describes this field as an anonymized user ID provided to MCP servers for
rate limiting and identification.

This is useful, but it is not authentication. It will not tell you a person's
name or email address, and it should never unlock private data.

## The short version

For each tool call:

1. Read `openai/subject` from the request metadata.
2. Turn it into your own anonymous customer key.
3. Store usage against that key.
4. Apply a small free allowance.
5. Treat missing or changed IDs as a normal case.

This gives you a practical anonymous identity without adding a signup screen at
the start.

## The familiar web app version

Web apps have used the same basic idea for years.

When someone visits an online shop, the site places a random visitor ID in a
browser cookie. The visitor has not created an account, but the shop can still
remember their cart and count how many free actions they have used. If the
visitor later signs in, the shop connects that guest activity to their account.

An MCP product follows the same pattern, with different parts:

| Standard web app | MCP product in ChatGPT |
| --- | --- |
| Anonymous visitor cookie | `openai/subject` |
| Browser session cookie | `openai/session` |
| Logged-in user ID | Validated OAuth `sub` |
| Browser sends requests | ChatGPT sends tool calls |
| Server checks trusted proxy or gateway | Server verifies ChatGPT with mTLS |

The main difference is who creates the anonymous ID. A website normally creates
and controls its own cookie. In the MCP flow, OpenAI creates
`openai/subject` and sends it to your server.

That means you can use the value, but you cannot control how long it lives or
when it changes.

## What ChatGPT sends

An MCP tool call can contain metadata like this:

```json
{
  "_meta": {
    "openai/subject": "v1/opaque-user-value",
    "openai/session": "v1/opaque-conversation-value",
    "openai/organization": "v1/opaque-organization-value"
  }
}
```

The three values have different jobs:

- `openai/subject` represents an anonymized user.
- `openai/session` represents a ChatGPT conversation.
- `openai/organization` represents the user's current ChatGPT organization,
  when one is available.

For a user-level allowance, start with `openai/subject`.

Do not use `openai/session` as the customer ID. A person can start a new
conversation and receive a new session value. Session IDs are useful for
debugging and for grouping calls from one conversation, but not for tracking a
free allowance across conversations.

This is similar to the difference between a visitor cookie and a browser tab.
The visitor may stay the same while individual browsing sessions come and go.

The [OpenAI Apps SDK
reference](https://developers.openai.com/apps-sdk/reference#_meta-fields-the-client-provides)
defines these fields and their intended uses.

## Create your own anonymous key

Do not use the raw subject value as a public customer ID. Store a one-way keyed
hash instead.

In plain terms, combine the subject with a private server secret:

```text
anonymous customer key =
    HMAC-SHA256(your private secret, "openai:" + openai/subject)
```

The result becomes the key in your usage database:

```text
anonymous_customer_key | successful_uses | period_started_at
abc123...              | 4               | 2026-07-01
```

Using a keyed hash has two benefits. A leaked database does not reveal the raw
OpenAI identifier, and the value cannot be reused to compare users across
unrelated systems.

This is the same separation a web app should make between a raw browser cookie
and its internal customer record. The value arriving from the client is an
input. Your own database key is the identity your system controls.

If your allowance should be separate for each ChatGPT workspace, include
`openai/organization`:

```text
HMAC-SHA256(
    your private secret,
    "openai:" + organization + ":" + subject
)
```

If the organization value is missing, use a clear placeholder instead of
rejecting the request.

## Count the thing that costs you money

A limit of "ten requests" is easy to explain, but it may not match your costs.
One request may perform a cheap database lookup while another starts a long
report.

Choose a unit that fits your product:

- completed searches;
- generated reports;
- processed documents;
- imported records;
- or simple credits, where expensive operations use more credits.

Count successful work, not every network attempt. MCP clients and gateways may
retry a request. Your usage system should avoid charging twice for an obvious
retry.

Keep the first version simple. For example:

```text
5 completed reports per anonymous user every 30 days
```

When no subject is present, either require signup or provide a much smaller
session-only allowance. Do not rely on IP addresses as the main fallback. The IP
seen by your server may belong to OpenAI, a proxy, a company network, Cloudflare,
or a VPN.

## The important disclaimer

An anonymous limit can be bypassed.

A person may use another ChatGPT account. OpenAI may change or re-scope an
anonymized ID. A caller may omit the field. Someone can also call a public MCP
endpoint directly and send a made-up `openai/subject`.

OpenAI does not publish a lifetime or rotation schedule for the subject value.
Design your database so a changed value creates a new anonymous visitor rather
than breaking your product.

The web equivalent is a person clearing their cookies or opening the site in a
different browser. The website sees a new guest even though the human is the
same. In the MCP world, another ChatGPT account or a changed subject can have
the same effect.

This makes `openai/subject` suitable for:

- a low-cost product trial;
- basic rate limiting;
- abuse reduction;
- and anonymous usage analytics.

It is not suitable for:

- protecting private customer records;
- paid entitlements;
- financial limits;
- account recovery;
- or security decisions.

Think of it as a durable visitor token, not a verified passport.

## Verify that the request came from ChatGPT

Before trusting OpenAI-specific metadata, verify that the caller is really
ChatGPT.

ChatGPT presents an OpenAI-managed client certificate when it opens a TLS
connection to an MCP server. Your server or network gateway can validate that
certificate with mutual TLS, usually shortened to mTLS.

Normal web HTTPS proves to a browser that it reached the right website. mTLS
adds proof in the other direction: the calling client also presents a
certificate to the server.

A simple analogy is a delivery driver arriving at a secure building. The
driver's company badge proves which delivery company sent them. It does not
prove who bought the package. In this case, mTLS proves that ChatGPT sent the
request, while OAuth later identifies the product user.

At the point where HTTPS is terminated:

1. Require a client certificate.
2. Verify that it chains to the OpenAI Connectors mTLS intermediate certificate.
3. Verify that the certificate is valid for client authentication.
4. Verify that its SAN DNS name is
   `mtls.prod.connectors.openai.com`.
5. Trust the published OpenAI certificate authorities, not one leaf certificate
   fingerprint.

OpenAI may rotate the leaf certificate. Pinning one certificate fingerprint can
therefore break a working integration. OpenAI publishes the certificate chain
and the current validation steps in its [Apps SDK authentication
guide](https://developers.openai.com/apps-sdk/build/auth#mutual-tls-mtls).

If Cloudflare, Nginx, or another load balancer handles HTTPS, mTLS verification
must happen there. The gateway should remove any identity headers supplied by
the public caller, add its own verified result, and send traffic to an origin
that cannot be reached directly. Otherwise, a caller could skip the gateway or
send a fake "verified" header.

OpenAI also publishes egress IP ranges that can be allowlisted, but mTLS gives
stronger proof of the client.

There is one boundary to remember:

> mTLS verifies ChatGPT as the client. It does not authenticate the human using
> ChatGPT.

When you need the identity of the human, use OAuth. That is the handoff from an
anonymous trial to a registered product account.

This is the same moment when a website turns a guest shopping cart into an
account cart after the visitor signs in.

## Keep the data collection clear

An anonymized ID is still user-related data. Explain what you collect, why you
collect it, and how long you keep it.

A short privacy statement could say:

> We store an anonymized identifier and usage count to provide a free allowance
> and prevent abuse. We do not use this identifier to discover your name or
> email address. Anonymous usage records are deleted after 90 days.

OpenAI's [app privacy
guidelines](https://developers.openai.com/apps-sdk/app-guidelines#privacy)
require clear disclosure, limited collection, retention information, and
meaningful user control. Collect what the product needs and leave the rest
alone.

## A sensible first version

A small MCP product can start with this policy:

```text
Verified ChatGPT request with subject:
    Allow 5 free operations per 30 days.

Verified ChatGPT request without subject:
    Allow 1 operation in the current session, then require signup.

Request not verified as ChatGPT:
    Require authentication or reject it.

Authenticated request:
    Use the product account ID from OAuth.
```

This will not stop every determined person from claiming another free trial. It
does not need to. Its job is to make the product easy to try while keeping casual
abuse and costs under control.

The next step is turning that limit into a clean signup moment. That is where an
anonymous MCP tool becomes a freemium MCP product.

## Official references

- [OpenAI Apps SDK: client-provided `_meta`
  fields](https://developers.openai.com/apps-sdk/reference#_meta-fields-the-client-provides)
- [OpenAI Apps SDK: client identification and
  mTLS](https://developers.openai.com/apps-sdk/build/auth#client-identification)
- [OpenAI Apps SDK: mutual
  TLS](https://developers.openai.com/apps-sdk/build/auth#mutual-tls-mtls)
- [OpenAI app privacy
  guidelines](https://developers.openai.com/apps-sdk/app-guidelines#privacy)
