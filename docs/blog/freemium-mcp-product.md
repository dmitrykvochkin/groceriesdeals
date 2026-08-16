# Freemium MCP product

Let people use your MCP product before they create an account. When they reach
the free limit, ask them to connect an account through OAuth.

That is the simplest freemium flow for an MCP product in ChatGPT:

```text
Try the product → use the free allowance → connect an account → keep going
```

The user sees value before seeing a signup screen. Your product still gets a
verified identity before it provides paid usage or private data.

This is not a new business model. It is the familiar web freemium flow moved
into ChatGPT.

| Standard web app | MCP product in ChatGPT |
| --- | --- |
| Browser cookie remembers a guest | `openai/subject` represents an anonymous user |
| Website counts free actions | MCP server counts completed tool operations |
| Website opens a signup modal | MCP server returns an OAuth challenge |
| Browser goes to the login page | ChatGPT opens the authorization flow |
| Website creates a login session | ChatGPT sends an OAuth access token |

The business logic stays on your server in both cases. The main change is that
ChatGPT, rather than your website, manages the user-facing connection flow.

## Start with anonymous usage

The first part of this model is covered in [User Identity without
signup](./user-identity-without-signup.md).

ChatGPT sends an anonymized user ID in
`_meta["openai/subject"]`. OpenAI says this value is intended for rate limiting
and identification. You can turn it into a private anonymous customer key and
store a usage count against it.

For example:

```text
Anonymous allowance: 5 completed reports
```

For each request, your MCP server makes one decision:

```text
Is there a valid OAuth token?
    Yes → use the registered account and its plan.
    No  → check the anonymous allowance.

Does the anonymous user have free usage left?
    Yes → run the tool and count the successful result.
    No  → ask ChatGPT to start account linking.
```

The free limit should be large enough to show the result people came for and
small enough that abuse does not become expensive. There is no universal number.
A product that searches an existing database can offer more free calls than a
product that runs a costly report.

On a normal website, this counter might be tied to a guest cookie. Here it is
tied to the anonymous key derived from `openai/subject`.

## Prepare OAuth before users hit the limit

ChatGPT cannot invent a signup flow for your product. Your MCP server must point
it to an OAuth 2.1 authorization server.

The authorization server can be provided by Auth0, Okta, Cognito, or another
established identity provider. It can also be part of your own product, but
building authentication from scratch adds security work that most teams do not
need.

Your signup and login pages live in that identity system. When a user connects
the MCP product, they are sent there to create an account or sign in.

This is the same division used by many web apps. The product owns the account,
while an identity provider handles passwords, login security, recovery, and
consent.

OpenAI's [Apps SDK authentication
guide](https://developers.openai.com/apps-sdk/build/auth) explains the required
OAuth 2.1 flow.

## Tell ChatGPT that authentication is available

ChatGPT shows its account-linking interface only when the MCP server provides
both setup information and a runtime authentication challenge.

There are three parts.

### 1. Publish protected resource metadata

Your MCP server needs a public metadata address such as:

```text
https://your-mcp.example.com/.well-known/oauth-protected-resource
```

The response tells ChatGPT:

- which resource is being protected;
- which authorization server to use;
- and which permission scopes are available.

A small example looks like this:

```json
{
  "resource": "https://your-mcp.example.com",
  "authorization_servers": ["https://auth.yourcompany.com"],
  "scopes_supported": ["reports:read"]
}
```

This is discovery information. It does not log the user in by itself.

In web terms, this file is a public sign-in map. It tells ChatGPT where login
happens and which permissions can be requested. It is closer to a configuration
file than a login page.

### 2. Mark the tool as optionally authenticated

During the free trial, the tool must work without an account. After signup, the
same tool can accept OAuth.

Describe both options in the tool's `securitySchemes`:

```json
[
  { "type": "noauth" },
  { "type": "oauth2", "scopes": ["reports:read"] }
]
```

`noauth` tells ChatGPT that anonymous calls are allowed. `oauth2` tells it that
account linking is also supported.

This combination fits a freemium tool. A tool that always handles private data
should advertise only OAuth and require login from the first call.

This is similar to marking website routes as public or protected. A product page
may be public, while `/account` requires login. In MCP, `securitySchemes`
describe that rule for each tool.

### 3. Return an authentication challenge at the limit

When the anonymous allowance reaches zero, do not return a generic "limit
exceeded" error. Return an MCP error result with
`_meta["mcp/www_authenticate"]`.

In simplified form:

```json
{
  "content": [
    {
      "type": "text",
      "text": "You have used your free reports. Connect an account to continue."
    }
  ],
  "_meta": {
    "mcp/www_authenticate": [
      "Bearer resource_metadata=\"https://your-mcp.example.com/.well-known/oauth-protected-resource\", error=\"insufficient_scope\", error_description=\"Connect an account to continue\""
    ]
  },
  "isError": true
}
```

The resource metadata, tool security scheme, and runtime challenge are all
required. Without the complete set, ChatGPT may show only an error instead of
the account-linking interface.

OpenAI documents this behavior in [Triggering authentication
UI](https://developers.openai.com/apps-sdk/build/auth#triggering-authentication-ui).

The closest web equivalent is returning `401 Unauthorized` and sending the
visitor to a login page. An MCP server does not control the ChatGPT screen
directly, so the challenge tells ChatGPT when to show its account-linking
experience.

## What the user experiences

Once the challenge is returned:

1. ChatGPT discovers your authorization server.
2. ChatGPT opens your login or signup page.
3. The user creates an account or signs in.
4. The user approves the requested permissions.
5. ChatGPT receives an access token.
6. ChatGPT retries later MCP calls with
   `Authorization: Bearer <token>`.

ChatGPT uses the authorization-code flow with PKCE. This protects the
authorization code while it moves between the browser, ChatGPT, and your
authorization server.

For readers used to web apps, ChatGPT is playing the role normally played by the
browser:

- your authorization server still shows the signup or login page;
- the user still gives consent;
- your authorization server still issues the token;
- and your backend still checks the token.

ChatGPT carries the result back to the MCP server instead of your website
creating a normal browser session.

The full sequence is shown in OpenAI's [OAuth flow
documentation](https://developers.openai.com/apps-sdk/build/auth#oauth-flow).

## Identify the registered user

After signup, stop using the anonymous subject as the main customer identity.

Verify the access token on every request. Check:

- the token signature;
- the issuer;
- the intended audience or resource;
- the expiration time;
- and the required permission scopes.

The validated token should contain a stable account identifier, normally the
`sub` claim:

```json
{
  "sub": "customer_123",
  "scope": "reports:read",
  "plan": "free"
}
```

Use that `sub` value to look up the user's product account and plan.

This matches a normal web backend. After login, the backend stops relying on a
guest cookie and uses the account ID stored in a signed session or validated
token.

In FastMCP, a configured authentication provider validates the token, and
request handlers can access the resulting token and claims. The important
product rule is simple: only validated claims can unlock registered or paid
usage.

## Carry the trial into the new account

The first authenticated request may still contain `openai/subject`. That gives
you a chance to connect the anonymous trial record to the new product account.

Online shops do this with guest carts. A visitor adds items before signing in.
After login, the shop moves or merges that guest cart into the account. Your MCP
product can do the same with anonymous usage history.

A safe linking process is:

1. Verify the OAuth token.
2. Read its stable account `sub`.
3. Calculate the same anonymous key used before signup.
4. Attach the anonymous usage record to the verified account.
5. Mark that anonymous record as claimed.

This prevents a person from receiving one anonymous allowance and then a second
fresh allowance immediately after signup, unless that is an intentional part of
your offer.

Do not accept an account ID as a normal tool argument and use it for linking.
Only the verified OAuth identity should decide which account receives the
history.

## Keep anonymous and registered limits separate

A simple plan table might look like this:

| User state | Identity source | Allowance |
| --- | --- | --- |
| Anonymous | Hashed `openai/subject` | 5 reports total |
| Registered free | Validated OAuth `sub` | 10 reports each month |
| Paid | Validated OAuth `sub` | Plan allowance |
| Missing identity | None | Signup required |

The anonymous allowance is a product preview. It is allowed to be imperfect.
The registered and paid limits must be enforced against verified accounts.

Keep the checks on the server. Tool descriptions and ChatGPT messages improve
the experience, but they are not enforcement.

## Make the limit feel fair

People should understand what happened and what they get by signing up.

A useful message says:

> You have used all 5 free reports. Connect an account to get 10 reports each
> month and keep your report history.

A poor message says:

> Error 429. Authentication required.

This follows the same rule as a good web paywall. Explain what ran out, what the
next step is, and what the person receives after signup.

Show the allowance before it runs out when possible:

```text
Report completed. You have 2 free reports left.
```

Count completed work rather than failed attempts. If the operation fails on your
side, return the credit. If clients retry the same request, avoid counting the
same work twice.

## Plan for bypasses

As explained in the first article, anonymous identity is not a hard security
boundary. A determined person may use another ChatGPT account, and anonymized
identifiers do not come with a published lifetime guarantee.

That is acceptable when:

- the trial cost is low;
- the limit mainly prevents casual overuse;
- and private or expensive features require OAuth.

If one anonymous operation is expensive, require signup earlier. If it exposes
private data or changes external systems, require signup from the start.

Also verify that unauthenticated requests really come from ChatGPT. OpenAI
supports client verification through mTLS. mTLS proves that ChatGPT is calling
your server; OAuth proves which product user is acting through ChatGPT. You need
both layers when identity matters.

## Respect the user's data

Tell users that you store an anonymized identifier and usage count before
signup. State the purpose, retention period, and deletion policy.

After signup, keep only the identity and usage information your product needs.
Do not turn technical metadata into hidden behavioral tracking.

OpenAI's [app privacy
guidelines](https://developers.openai.com/apps-sdk/app-guidelines#privacy)
require limited collection, a clear privacy policy, and meaningful user
control.

## The complete model

The finished flow looks like this:

```text
Tool call arrives
    |
    |-- Valid OAuth token?
    |       |
    |       `-- Yes: verify token, identify account, apply account plan
    |
    `-- No: verify ChatGPT client, read anonymous subject
            |
            |-- Free usage remains: run tool and count success
            |
            `-- Limit reached: return OAuth challenge
                                |
                                `-- User signs up and continues
```

This is enough to build a freemium MCP product that is easy to try and has a
clear path to signup. Anonymous identity reduces friction. OAuth provides the
identity needed for accounts, private data, and billing.

## Official references

- [OpenAI Apps SDK: client-provided `_meta`
  fields](https://developers.openai.com/apps-sdk/reference#_meta-fields-the-client-provides)
- [OpenAI Apps SDK:
  authentication](https://developers.openai.com/apps-sdk/build/auth)
- [OpenAI Apps SDK: triggering authentication
  UI](https://developers.openai.com/apps-sdk/build/auth#triggering-authentication-ui)
- [OpenAI Apps SDK: OAuth
  flow](https://developers.openai.com/apps-sdk/build/auth#oauth-flow)
- [OpenAI app privacy
  guidelines](https://developers.openai.com/apps-sdk/app-guidelines#privacy)
