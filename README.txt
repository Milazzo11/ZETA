ZETA (Zero-storage Encrypted Ticket Authentication) is a secure authentication API for minimal-state ticket issuance, transfer, cancelation, redemption, and validation in event management and access control systems.  It leverages Kerberos-inspired symmetric-key ticket encryption with embedded custom metadata support, yielding zero server-side user data storage (and only a single byte per ticket used for state management).

Each ticket is encrypted to the holder and validated by the server on demand.  The system prevents double-use, spoofing, unauthorized transfers, and replay attacks, while keeping the protocol lightweight and easy to reason about.  Mutual authentication is achieved without requiring long-term session cookies or tokens.


Requirements:
=============
- Python (built on 3.13.7)
- PostgreSQL (built on 18.0)
- *Redis (built on 7.0.15) -- Redis is used for temporary nonce tracking to prevent replay attacks, but a "Redis-less" naive option is available to configure as well...  HOWEVER, multiple pods/replicas cannot securely run in this mode.


API Endpoints:
==============
/create -- When creating an event, the owner chooses parameters like ticket count, restricted or open access, and start and end time.  Once created, the event becomes available for searching and registration.  The owner holds special authority and can grant some access to other authorized parties as well.

/search -- The search endpoint allows users to look up events by ID or text.  It returns basic public information about matching events.  This is not authenticated beyond request signing, and it never reveals secret state, keys, or ticket details.

/register -- The registration endpoint issues a ticket to the requesting public key.  For open events, registration succeeds automatically until capacity is reached.  However, for restricted events, the requester must present a signed verification token from the event owner or an authorized party.  If desired, the authorizer can also embed custom ticket metadata within this verification block.

/transfer -- The transfer endpoint lets a user assign a ticket to another public key.  The current holder signs a transfer verification token naming the new holder; the new holder then presents this proof when claiming the ticket.  The system updates the ticket version and marks the old version invalid.  This prevents double-use or replay of earlier ticket copies.

/redeem -- The redeem endpoint allows the ticket holder to prove possession and request redemption.  The holder signs the request with his key and submits the encrypted ticket.  The server confirms the ticket belongs to him and has not been used or canceled.

/validate -- The validate endpoint allows the event owner or an authorized party to check the ticket state and optionally stamp it.  Stamping finalizes the redemption and prevents future reuse.  Any user can also verify a ticket's content without stamping, but stamping is what enforces the one-use rule.  Users without special authorization, however, cannot see stamp status and cannot modify state.

/flag -- The flag endpoint allows an event owner or an authorized party to attach a compact application-defined flag to a specific ticket number.  The flag is a 0-127 value stored in a single byte of per-ticket state and can be used to track custom workflows.  Owners and authorized parties can update a flag value and control whether it is publicly visible; other parties may only read public flag values and can never change them.

/cancel -- The cancel endpoint allows an event owner or authorized party to invalidate a ticket.  Once canceled, the ticket can no longer be redeemed, stamped, or transferred.  Cancellation is final.

/delete -- The delete endpoint allows an event owner to remove his event from the server.

/permissions -- The permissions endpoint allows an event owner to delegate event-management capabilities to additional public keys.  For a given event, the owner can configure whether a key is allowed to cancel tickets, view non-public flags, update flags, authorize restricted registrations, view stamped status, and stamp tickets.  This endpoint is owner-protected and returns a signed description of the effective permission set, enabling fine-grained access control.


Every endpoint returns a signed response so the client cannot be fooled by network tampering or fake error messages.  If an action fails, the server signs the failure result as well.  Each request also includes a nonce and timestamp to block replay attacks.

The system is designed to make cheating impossible through simple cryptographic enforcement rather than complex infrastructure.  If a user does not have the right key or tries to reuse a ticket, the server rejects it.  All client-held data is considered untrusted until validated with signatures and decryption.  Because the server stores minimal state and ticket checks are constant-time bit reads, the system remains efficient and scalable.