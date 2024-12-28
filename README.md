# POST App

This application is designed to handle posts and provide post rating to users.

## The Main Design:

- Posts are cached using Redis for 1 day, and their content is provided from there.
- Their rating data is calculated on Redis, and users will see the live data.
- Posts are persisted in the database at specific periods using Celery tasks.
- If Redis data are missed, at worst case, rate calculations of about 30 seconds will be missed.

- User Rating endpoint persists the user's rate and triggers a Celery task to recalculate the post average rate.
- If Redis is lost, they will be warmed up from the last state persisted in the database.

### Rate Limiting Mechanism:

For handling abnormal user behaviors, a rate-limiting mechanism is developed, which works as follows:

1. **Request Rate Storage:**
    - Store request rates per post for 1-hour buckets.
    - To calculate the current rate, we get:
      ```
      Current bucket value + (Percentage of time remaining from the bucket before * The bucket’s rate)
      ```
      For example:
        - Imagine we are at 02:25. The value will be:
          ```
          (02 bucket value + (01 bucket value * ((60 - 25)/60)))
          ```
    - The idea comes from the sliding window approach but is not entirely accurate. The point is that it uses much less
      memory
      space to store data than the exact sliding window.

2. **Rate Rules:**
    - In this project, each post can have rates up to **30% more** than the bucket before.
    - For example, if a post had 3,000 rates from 2:00 to 3:00, it can have up to:
      ```
      3,000 * 1.3 = 3,900
      ```
      for the next hour bucket.
    - A minimum of **1,000** is defined for the first or empty request time buckets.
    - Each user can submit up to **5 rates per hour**.

3. **Integration & Scalability:**
    - The rate-limiting logic is integrated into the application and uses the application’s default Redis instance but
      to avoid affecting the application Redis performance, it is possible to provide another Redis instance for it; and
      for better separation of concerns, the rate limiter could be made into another service that provides service to
      the application.
    - The rate-limiting logic will not affect the application logic when it faces failures. This approach is not secure
      enough but guarantees the application’s uptime.

> **Note:** The authentication server is assumed to perform before the service call, and the user ID is sent via the
> header `X-User-Id`.

---

## Technologies:

- **Kafka** is chosen as the Celery broker for its scalability and fault tolerance compared to other choices.
- **Redis** is used for:
    - Caches
    - Some application-level distributed locks
    - Rate limiting
- **PostgreSQL** is chosen as the SQL database.

---

## Endpoints:

### 1. `GET /posts`

- If the user is authenticated, the user’s rates will be shown.

#### Sample Request:

```bash
curl --location 'http://127.0.0.1:8000/posts' \
--header 'X-User-Id: 2'
```

- Sample Response:

```json 
{
  "next": null,
  "previous": null,
  "results": [
    {
      "title": "First Title",
      "text": "First post text",
      "rate": 2.8,
      "rate_count": 27700,
      "user_rate": null
    },
    {
      "title": "rg7fbrtu",
      "text": "ghyhubjjjjjjj,dndbvcxbghnjkjxhcgvfbnmdxkjuhyuidfktmjnmjfchghjnmfvg mhykjgbfvchbft",
      "rate": 3.4,
      "rate_count": 27518,
      "user_rate": 4
    }
  ]
}
```

- The pagination logic is based on cursor pagination due to better database performance

### 2. `POST /posts/<post_id>/rate`

- This endpoint requires authentication, the user id header should be provided.

#### Sample Request:

```bash 
curl --location 'http://127.0.0.1:8000/posts/3/rate' \
      --header 'X-User-Id: 6' \
      --header 'Content-Type: application/json' \
      --data '{
      "rate":4
      }'
```

#### Sample Response:

```json
{
  "detail": "Submitted successfully"
}
```