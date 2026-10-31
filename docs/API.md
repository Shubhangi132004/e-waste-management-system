# EcoSmart API reference

All JSON state-changing requests require the `X-CSRFToken` header returned by `GET /api/csrf-token`. Browser session authentication is cookie-based.

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| GET | `/api/csrf-token` | Public | Creates/returns a CSRF token |
| POST | `/api/auth/register` | Public | Registers a normal user; never accepts a role |
| POST | `/api/auth/login` | Public | Starts a session |
| POST | `/api/auth/logout` | Authenticated | Ends a session |
| GET | `/api/auth/me` | Public | Returns current session information |
| POST | `/api/reports` | Public or authenticated | Creates a validated e-waste report |
| GET | `/api/reports` | Authenticated | Returns the current user's reports |
| GET | `/api/stats` | Public | Returns live counts and grouped analytics |
| GET | `/api/admin/reports` | Admin | Search/filter all reports |
| PUT | `/api/admin/reports/<id>` | Admin | Update `Pending`, `In Progress`, or `Resolved` |
| DELETE | `/api/admin/reports/<id>` | Admin | Delete a report and clean up its image |
| POST | `/api/collections` | Authenticated | Create a collection request |
| GET | `/api/collections` | Authenticated | Return own requests, or all requests for admin |
| PUT | `/api/admin/collections/<id>` | Admin | Update collection status |

Report categories are `Mobile Phones`, `Laptops`, `Batteries`, `Chargers`, `Computer Accessories`, `Televisions`, and `Other Electronic Waste`. Uploaded images are limited to 5 MB and safe image extensions.
