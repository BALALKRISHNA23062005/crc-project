# CRC Application Architecture

## Main parts

- `members` handles signup, login, and the club member profile.
- `events` handles events, registrations, QR codes, payment, check-in, and the organizer roster.
- `crc_system` contains Django settings and the top-level URL routing.
- Django admin provides staff with management screens for the records.
- SQLite is the local database. The hosted service uses PostgreSQL. Whitenoise serves collected static files.

## Data relationships in plain language

- Django's built-in `User` holds login credentials. Each `Member` profile belongs to one `User`; a user has at most one member profile.
- A `Member` can have registrations for multiple events. An `Event` can have registrations from multiple members. `Registration` connects one member to one event and stores the registration time, payment status, QR code, and Razorpay order ID.
- The registration view blocks duplicate registrations and prevents new registrations when an event reaches its capacity.
- An `Event` stores its title, date, location, participant limit, and fee. Free events are marked paid/not applicable without creating a Razorpay checkout.
- A `Payment` record refers to a registration and stores the amount, transaction ID, and payment time. A successful paid checkout is recorded only after Razorpay signature verification.
- An `Attendance` record refers to a registration and stores when it was checked in. The check-in view avoids recording a second check-in through the normal QR flow.

In relationship notation:

```text
User 1 --- 1 Member
Member 1 --- many Registration many --- 1 Event
Registration 1 --- many Payment
Registration 1 --- many Attendance
```

The foreign-key relationships to `Payment` and `Attendance` allow more than one row at the database level, even though the application flow records a payment once and prevents repeated check-ins.

## Main request flows

1. A member signs up and receives a `User` login plus a `Member` profile.
2. The member chooses an upcoming event. The app checks capacity and creates a `Registration` with a generated QR code.
3. Free registrations are marked paid/not applicable. For a paid event, the member starts Razorpay checkout; the return request must match the stored order ID and pass signature verification before payment status changes.
4. The member's QR code points to the check-in URL. A logged-in staff user can scan it; non-staff users are denied.
5. A staff user can open an event's organizer page to review registration, payment, and attendance status and counts.

## Access boundaries

- Registration, QR, and payment pages are restricted to the owning member.
- Check-in and organizer pages require a staff account.
- Payment confirmation uses Razorpay signature verification; query parameters alone do not mark a registration paid.