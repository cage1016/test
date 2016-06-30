#cheerspoint tasks module

###Download data from GAE server and import to development

####Step 1: setup app.yaml

add remote_api endpoint at `app.yaml`

```yaml
...
builtins:
- remote_api: on
...
```

####Step 2: Download data

```
Usage: appcfg.py [options] download_data <directory>

Download entities from datastore.

The 'download_data' command downloads datastore entities and writes them to
file as CSV or developer defined format.

Options:
  -h, --help            Show the help message and exit.
  -q, --quiet           Print errors only.
  -v, --verbose         Print info level logs.
  --noisy               Print all logs.
  -s SERVER, --server=SERVER
                        The App Engine server.
  -e EMAIL, --email=EMAIL
                        The username to use. Will prompt if omitted.
  -H HOST, --host=HOST  Overrides the Host header sent with all RPCs.
  --no_cookies          Do not save authentication cookies to local disk.
  --skip_sdk_update_check
                        Do not check for SDK updates.
  --passin              Read the login password from stdin.
  -A APP_ID, --application=APP_ID
                        Set the application, overriding the application value
                        from app.yaml file.
  -M MODULE, --module=MODULE
                        Set the module, overriding the module value from
                        app.yaml.
  -V VERSION, --version=VERSION
                        Set the (major) version, overriding the version value
                        from app.yaml file.
  -r RUNTIME, --runtime=RUNTIME
                        Override runtime from app.yaml file.
  -E NAME:VALUE, --env_variable=NAME:VALUE
                        Set an environment variable, potentially overriding an
                        env_variable value from app.yaml file (flag may be
                        repeated to set multiple variables).
  -R, --allow_any_runtime
                        Do not validate the runtime in app.yaml
  --oauth2              Ignored (OAuth2 is the default).
  --no_oauth2           Use password auth instead of OAuth2.
  --oauth2_refresh_token=OAUTH2_REFRESH_TOKEN
                        An existing OAuth2 refresh token to use. Will not
                        attempt interactive OAuth approval.
  --oauth2_access_token=OAUTH2_ACCESS_TOKEN
                        An existing OAuth2 access token to use. Will not
                        attempt interactive OAuth approval.
  --authenticate_service_account
                        Authenticate using the default service account for the
                        Google Compute Engine VM in which appcfg is being
                        called
  --noauth_local_webserver
                        Do not run a local web server to handle redirects
                        during OAuth authorization.
  --url=URL             The location of the remote_api endpoint.
  --batch_size=BATCH_SIZE
                        Number of records to post in each request.
  --bandwidth_limit=BANDWIDTH_LIMIT
                        The maximum bytes/second bandwidth for transfers.
  --rps_limit=RPS_LIMIT
                        The maximum records/second for transfers.
  --http_limit=HTTP_LIMIT
                        The maximum requests/second for transfers.
  --db_filename=DB_FILENAME
                        Name of the progress database file.
  --auth_domain=AUTH_DOMAIN
                        The name of the authorization domain to use.
  --log_file=LOG_FILE   File to write bulkloader logs.  If not supplied then a
                        new log file will be created, named: bulkloader-log-
                        TIMESTAMP.
  --dry_run             Do not execute any remote_api calls
  --namespace=NAMESPACE
                        Namespace to use when accessing datastore.
  --num_threads=NUM_THREADS
                        Number of threads to transfer records with.
  --filename=FILENAME   The name of the file where output data is to be
                        written. (Required)
  --kind=KIND           The kind of the entities to retrieve.
  --exporter_opts=EXPORTER_OPTS
                        A string to pass to the Exporter.initialize method.
  --result_db_filename=RESULT_DB_FILENAME
                        Database to write entities to for download.
  --config_file=CONFIG_FILE
                        Name of the configuration file.
```

```sh
appcfg.py --application=s~cage-20160705-edm --url=https://cage-20160705-edm.appspot.com/_ah/remote_api/ --filename=logemails.csv --kind=LogEmail --skip_sdk_update_check download_data .
```

####Step 3: import data to development server

```sh
appcfg.py upload_data --url=http://localhost:8080/_ah/remote_api --filename=bulkloader-results-20150610.092142.sql3 --application=dev~cage-20160705-edm
```
