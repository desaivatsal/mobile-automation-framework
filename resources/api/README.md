# API layer (extension point)

Nothing here runs yet. Same rationale as `resources/web/`: the seams exist so
API suites are an addition, not a rewrite.

## What is already in place

- `config/default.yaml` and every environment file carry an `api:` block
  (`base_url`, `timeout`, `verify_ssl`), surfaced as `${API_BASE_URL}`.
- `requirements-api.txt` pins `robotframework-requests`, `JSONLibrary` and
  `jsonschema`.
- `tests/api/` is the suite root.

## How to add the first API test

1. `pip install -r requirements-api.txt`
2. Create `resources/api/api_session.resource` holding `Create Session` and auth
   keywords — the API equivalent of `resources/common/session.resource`.
3. Put request builders in `resources/api/services/<service>_service.resource`.
   Tests assert; services call. Same boundary as the mobile page objects.
4. Keep response schemas in `testdata/schemas/` and validate with `jsonschema`
   rather than asserting field by field.
5. Add an `api` job to `.github/workflows/regression.yml`. API tests need no
   Sauce credentials, so that job should run on every PR — it is the cheapest
   signal in the suite.

See `tests/api/example_api_tests.robot.example` for the shape of a suite.
