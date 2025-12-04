---
title: HumAL API v1.0.0
language_tabs:
  - shell: Shell
  - http: HTTP
  - javascript: JavaScript
  - ruby: Ruby
  - python: Python
  - php: PHP
  - java: Java
  - go: Go
toc_footers: []
includes: []
search: true
highlight_theme: darkula
headingLevel: 2

---

<!-- Generator: Widdershins v4.0.1 -->

<h1 id="humal-api">HumAL API v1.0.0</h1>

> Scroll down for code samples, example requests and responses. Select a language for code samples from the tabs above or the mobile navigation menu.

Human-in-the-loop Active Learning API

<h1 id="humal-api-inference">inference</h1>

## infer_activelearning__al_instance_id__infer_post

<a id="opIdinfer_activelearning__al_instance_id__infer_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /activelearning/{al_instance_id}/infer \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /activelearning/{al_instance_id}/infer HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/activelearning/{al_instance_id}/infer',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/activelearning/{al_instance_id}/infer',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/activelearning/{al_instance_id}/infer', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/activelearning/{al_instance_id}/infer', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/{al_instance_id}/infer");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/activelearning/{al_instance_id}/infer", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /activelearning/{al_instance_id}/infer`

*Infer*

> Body parameter

```json
{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}
```

<h3 id="infer_activelearning__al_instance_id__infer_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|body|body|[Data](#schemadata)|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="infer_activelearning__al_instance_id__infer_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="infer_activelearning__al_instance_id__infer_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="humal-api-active_learning">active_learning</h1>

## activelearning_init_activelearning_new_post

<a id="opIdactivelearning_init_activelearning_new_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /activelearning/new \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /activelearning/new HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "model_name": "string",
  "qs_strategy": "string",
  "class_list": [
    0
  ],
  "train_data_path": "string",
  "test_data_path": "string"
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/activelearning/new',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/activelearning/new',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/activelearning/new', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/activelearning/new', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/new");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/activelearning/new", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /activelearning/new`

*Activelearning Init*

> Body parameter

```json
{
  "model_name": "string",
  "qs_strategy": "string",
  "class_list": [
    0
  ],
  "train_data_path": "string",
  "test_data_path": "string"
}
```

<h3 id="activelearning_init_activelearning_new_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[NewInstance](#schemanewinstance)|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="activelearning_init_activelearning_new_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="activelearning_init_activelearning_new_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## next_instance_activelearning__al_instance_id__next_get

<a id="opIdnext_instance_activelearning__al_instance_id__next_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /activelearning/{al_instance_id}/next \
  -H 'Accept: application/json'

```

```http
GET /activelearning/{al_instance_id}/next HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/activelearning/{al_instance_id}/next',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/activelearning/{al_instance_id}/next',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/activelearning/{al_instance_id}/next', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/activelearning/{al_instance_id}/next', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/{al_instance_id}/next");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/activelearning/{al_instance_id}/next", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /activelearning/{al_instance_id}/next`

*Next Instance*

<h3 id="next_instance_activelearning__al_instance_id__next_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|batch_size|query|integer|false|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="next_instance_activelearning__al_instance_id__next_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="next_instance_activelearning__al_instance_id__next_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## label_instance_activelearning__al_instance_id__label_put

<a id="opIdlabel_instance_activelearning__al_instance_id__label_put"></a>

> Code samples

```shell
# You can also use wget
curl -X PUT /activelearning/{al_instance_id}/label \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
PUT /activelearning/{al_instance_id}/label HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "query_idx": [
    0
  ],
  "labels": [
    "string"
  ]
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/activelearning/{al_instance_id}/label',
{
  method: 'PUT',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.put '/activelearning/{al_instance_id}/label',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.put('/activelearning/{al_instance_id}/label', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('PUT','/activelearning/{al_instance_id}/label', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/{al_instance_id}/label");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("PUT");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("PUT", "/activelearning/{al_instance_id}/label", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`PUT /activelearning/{al_instance_id}/label`

*Label Instance*

> Body parameter

```json
{
  "query_idx": [
    0
  ],
  "labels": [
    "string"
  ]
}
```

<h3 id="label_instance_activelearning__al_instance_id__label_put-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|body|body|[LabelRequest](#schemalabelrequest)|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="label_instance_activelearning__al_instance_id__label_put-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="label_instance_activelearning__al_instance_id__label_put-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## get_info_activelearning__al_instance_id__info_get

<a id="opIdget_info_activelearning__al_instance_id__info_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /activelearning/{al_instance_id}/info \
  -H 'Accept: application/json'

```

```http
GET /activelearning/{al_instance_id}/info HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/activelearning/{al_instance_id}/info',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/activelearning/{al_instance_id}/info',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/activelearning/{al_instance_id}/info', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/activelearning/{al_instance_id}/info', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/{al_instance_id}/info");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/activelearning/{al_instance_id}/info", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /activelearning/{al_instance_id}/info`

*Get Info*

<h3 id="get_info_activelearning__al_instance_id__info_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="get_info_activelearning__al_instance_id__info_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="get_info_activelearning__al_instance_id__info_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## save_model_activelearning__al_instance_id__save_post

<a id="opIdsave_model_activelearning__al_instance_id__save_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /activelearning/{al_instance_id}/save \
  -H 'Accept: application/json'

```

```http
POST /activelearning/{al_instance_id}/save HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/activelearning/{al_instance_id}/save',
{
  method: 'POST',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.post '/activelearning/{al_instance_id}/save',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.post('/activelearning/{al_instance_id}/save', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/activelearning/{al_instance_id}/save', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/{al_instance_id}/save");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/activelearning/{al_instance_id}/save", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /activelearning/{al_instance_id}/save`

*Save Model*

<h3 id="save_model_activelearning__al_instance_id__save_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="save_model_activelearning__al_instance_id__save_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="save_model_activelearning__al_instance_id__save_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## get_instances_activelearning_instances_get

<a id="opIdget_instances_activelearning_instances_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /activelearning/instances \
  -H 'Accept: application/json'

```

```http
GET /activelearning/instances HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/activelearning/instances',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/activelearning/instances',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/activelearning/instances', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/activelearning/instances', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/instances");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/activelearning/instances", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /activelearning/instances`

*Get Instances*

> Example responses

> 200 Response

```json
null
```

<h3 id="get_instances_activelearning_instances_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

<h3 id="get_instances_activelearning_instances_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## delete_instance_activelearning__al_instance_id__delete

<a id="opIddelete_instance_activelearning__al_instance_id__delete"></a>

> Code samples

```shell
# You can also use wget
curl -X DELETE /activelearning/{al_instance_id} \
  -H 'Accept: application/json'

```

```http
DELETE /activelearning/{al_instance_id} HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/activelearning/{al_instance_id}',
{
  method: 'DELETE',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.delete '/activelearning/{al_instance_id}',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.delete('/activelearning/{al_instance_id}', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('DELETE','/activelearning/{al_instance_id}', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/activelearning/{al_instance_id}");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("DELETE");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("DELETE", "/activelearning/{al_instance_id}", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`DELETE /activelearning/{al_instance_id}`

*Delete Instance*

<h3 id="delete_instance_activelearning__al_instance_id__delete-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="delete_instance_activelearning__al_instance_id__delete-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="delete_instance_activelearning__al_instance_id__delete-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="humal-api-configuration">configuration</h1>

## get_available_models_config_models_get

<a id="opIdget_available_models_config_models_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /config/models \
  -H 'Accept: application/json'

```

```http
GET /config/models HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/config/models',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/config/models',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/config/models', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/config/models', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/config/models");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/config/models", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /config/models`

*Get Available Models*

Get all available machine learning model names.

Returns:
    Dictionary containing model names

> Example responses

> 200 Response

```json
null
```

<h3 id="get_available_models_config_models_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

<h3 id="get_available_models_config_models_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## get_available_query_strategies_config_query_strategies_get

<a id="opIdget_available_query_strategies_config_query_strategies_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /config/query-strategies \
  -H 'Accept: application/json'

```

```http
GET /config/query-strategies HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/config/query-strategies',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/config/query-strategies',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/config/query-strategies', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/config/query-strategies', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/config/query-strategies");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/config/query-strategies", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /config/query-strategies`

*Get Available Query Strategies*

Get all available query strategy names.

Returns:
    Dictionary containing query strategy names

> Example responses

> 200 Response

```json
null
```

<h3 id="get_available_query_strategies_config_query_strategies_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|

<h3 id="get_available_query_strategies_config_query_strategies_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="humal-api-data">data</h1>

## get_tickets_data__al_instance_id__tickets_post

<a id="opIdget_tickets_data__al_instance_id__tickets_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /data/{al_instance_id}/tickets \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /data/{al_instance_id}/tickets HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '[
  "string"
]';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/data/{al_instance_id}/tickets',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/data/{al_instance_id}/tickets',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/data/{al_instance_id}/tickets', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/data/{al_instance_id}/tickets', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/data/{al_instance_id}/tickets");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/data/{al_instance_id}/tickets", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /data/{al_instance_id}/tickets`

*Get Tickets*

Get tickets by their indices.

Returns:
    Dictionary containing tickets

> Body parameter

```json
[
  "string"
]
```

<h3 id="get_tickets_data__al_instance_id__tickets_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|train_data_path|query|string|false|none|
|body|body|array[string]|true|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="get_tickets_data__al_instance_id__tickets_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="get_tickets_data__al_instance_id__tickets_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## get_teams_data__al_instance_id__teams_get

<a id="opIdget_teams_data__al_instance_id__teams_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /data/{al_instance_id}/teams \
  -H 'Accept: application/json'

```

```http
GET /data/{al_instance_id}/teams HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/data/{al_instance_id}/teams',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/data/{al_instance_id}/teams',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/data/{al_instance_id}/teams', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/data/{al_instance_id}/teams', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/data/{al_instance_id}/teams");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/data/{al_instance_id}/teams", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /data/{al_instance_id}/teams`

*Get Teams*

Get teams from the dataset.
If al_instance_id is 0, the train_data_path is required.    

Returns:
    Dictionary containing teams

<h3 id="get_teams_data__al_instance_id__teams_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|train_data_path|query|string|false|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="get_teams_data__al_instance_id__teams_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="get_teams_data__al_instance_id__teams_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## get_categories_data__al_instance_id__categories_get

<a id="opIdget_categories_data__al_instance_id__categories_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /data/{al_instance_id}/categories \
  -H 'Accept: application/json'

```

```http
GET /data/{al_instance_id}/categories HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/data/{al_instance_id}/categories',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/data/{al_instance_id}/categories',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/data/{al_instance_id}/categories', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/data/{al_instance_id}/categories', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/data/{al_instance_id}/categories");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/data/{al_instance_id}/categories", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /data/{al_instance_id}/categories`

*Get Categories*

Get categories from the dataset.

Returns:
    Dictionary containing categories

<h3 id="get_categories_data__al_instance_id__categories_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|train_data_path|query|string|false|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="get_categories_data__al_instance_id__categories_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="get_categories_data__al_instance_id__categories_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## get_subcategories_data__al_instance_id__subcategories_get

<a id="opIdget_subcategories_data__al_instance_id__subcategories_get"></a>

> Code samples

```shell
# You can also use wget
curl -X GET /data/{al_instance_id}/subcategories \
  -H 'Accept: application/json'

```

```http
GET /data/{al_instance_id}/subcategories HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/data/{al_instance_id}/subcategories',
{
  method: 'GET',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.get '/data/{al_instance_id}/subcategories',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.get('/data/{al_instance_id}/subcategories', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('GET','/data/{al_instance_id}/subcategories', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/data/{al_instance_id}/subcategories");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("GET");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("GET", "/data/{al_instance_id}/subcategories", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`GET /data/{al_instance_id}/subcategories`

*Get Subcategories*

Get subcategories from the dataset.

Returns:
    Dictionary containing subcategories

<h3 id="get_subcategories_data__al_instance_id__subcategories_get-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|train_data_path|query|string|false|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="get_subcategories_data__al_instance_id__subcategories_get-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="get_subcategories_data__al_instance_id__subcategories_get-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="humal-api-xai">xai</h1>

## explain_lime_xai__al_instance_id__explain_lime_post

<a id="opIdexplain_lime_xai__al_instance_id__explain_lime_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /xai/{al_instance_id}/explain_lime \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /xai/{al_instance_id}/explain_lime HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/xai/{al_instance_id}/explain_lime',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/xai/{al_instance_id}/explain_lime',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/xai/{al_instance_id}/explain_lime', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/xai/{al_instance_id}/explain_lime', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/xai/{al_instance_id}/explain_lime");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/xai/{al_instance_id}/explain_lime", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /xai/{al_instance_id}/explain_lime`

*Explain Lime*

> Body parameter

```json
{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}
```

<h3 id="explain_lime_xai__al_instance_id__explain_lime_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|query_idx|query|any|false|none|
|model_id|query|integer|false|none|
|body|body|any|false|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="explain_lime_xai__al_instance_id__explain_lime_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="explain_lime_xai__al_instance_id__explain_lime_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

## find_nearest_ticket_xai__al_instance_id__nearest_ticket_post

<a id="opIdfind_nearest_ticket_xai__al_instance_id__nearest_ticket_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /xai/{al_instance_id}/nearest_ticket \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /xai/{al_instance_id}/nearest_ticket HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/xai/{al_instance_id}/nearest_ticket',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/xai/{al_instance_id}/nearest_ticket',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/xai/{al_instance_id}/nearest_ticket', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/xai/{al_instance_id}/nearest_ticket', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/xai/{al_instance_id}/nearest_ticket");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/xai/{al_instance_id}/nearest_ticket", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /xai/{al_instance_id}/nearest_ticket`

*Find Nearest Ticket*

> Body parameter

```json
{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}
```

<h3 id="find_nearest_ticket_xai__al_instance_id__nearest_ticket_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|al_instance_id|path|integer|true|none|
|query_idx|query|any|false|none|
|model_id|query|integer|false|none|
|body|body|any|false|none|

> Example responses

> 200 Response

```json
null
```

<h3 id="find_nearest_ticket_xai__al_instance_id__nearest_ticket_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|Inline|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<h3 id="find_nearest_ticket_xai__al_instance_id__nearest_ticket_post-responseschema">Response Schema</h3>

<aside class="success">
This operation does not require authentication
</aside>

<h1 id="humal-api-resolution">resolution</h1>

## process_ticket_resolution_resolution_process_post

<a id="opIdprocess_ticket_resolution_resolution_process_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /resolution/process \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /resolution/process HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "ticket_title": "string",
  "ticket_description": "string",
  "service_category": "string",
  "service_subcategory": "string",
  "top_k": 3,
  "force_rebuild": false
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/resolution/process',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/resolution/process',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/resolution/process', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/resolution/process', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/resolution/process");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/resolution/process", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /resolution/process`

*Process Ticket Resolution*

Generate first-reply response for IT support ticket.
Uses RAG + GPT to generate contextually appropriate responses.

> Body parameter

```json
{
  "ticket_title": "string",
  "ticket_description": "string",
  "service_category": "string",
  "service_subcategory": "string",
  "top_k": 3,
  "force_rebuild": false
}
```

<h3 id="process_ticket_resolution_resolution_process_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[ResolutionRequest](#schemaresolutionrequest)|true|none|

> Example responses

> 200 Response

```json
{
  "classification": "string",
  "predicted_team": "string",
  "team_confidence": 0,
  "response": "string",
  "similar_replies": [
    {}
  ],
  "retrieval_k": 0
}
```

<h3 id="process_ticket_resolution_resolution_process_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|[ResolutionResponse](#schemaresolutionresponse)|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<aside class="success">
This operation does not require authentication
</aside>

## save_ticket_feedback_resolution_feedback_post

<a id="opIdsave_ticket_feedback_resolution_feedback_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /resolution/feedback \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json'

```

```http
POST /resolution/feedback HTTP/1.1

Content-Type: application/json
Accept: application/json

```

```javascript
const inputBody = '{
  "ticket_title": "string",
  "ticket_description": "string",
  "edited_response": "string",
  "predicted_team": "string",
  "predicted_classification": "string",
  "service_name": "string",
  "service_subcategory": "string"
}';
const headers = {
  'Content-Type':'application/json',
  'Accept':'application/json'
};

fetch('/resolution/feedback',
{
  method: 'POST',
  body: inputBody,
  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Content-Type' => 'application/json',
  'Accept' => 'application/json'
}

result = RestClient.post '/resolution/feedback',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}

r = requests.post('/resolution/feedback', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Content-Type' => 'application/json',
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/resolution/feedback', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/resolution/feedback");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Content-Type": []string{"application/json"},
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/resolution/feedback", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /resolution/feedback`

*Save Ticket Feedback*

Save resolved ticket for continuous improvement.
Adds single embedding to FAISS index without full rebuild.

> Body parameter

```json
{
  "ticket_title": "string",
  "ticket_description": "string",
  "edited_response": "string",
  "predicted_team": "string",
  "predicted_classification": "string",
  "service_name": "string",
  "service_subcategory": "string"
}
```

<h3 id="save_ticket_feedback_resolution_feedback_post-parameters">Parameters</h3>

|Name|In|Type|Required|Description|
|---|---|---|---|---|
|body|body|[FeedbackRequest](#schemafeedbackrequest)|true|none|

> Example responses

> 200 Response

```json
{
  "success": true,
  "message": "string",
  "ticket_ref": "string",
  "new_kb_size": 0,
  "embedding_added_incrementally": true,
  "embedding_invalidated": true
}
```

<h3 id="save_ticket_feedback_resolution_feedback_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|[FeedbackResponse](#schemafeedbackresponse)|
|422|[Unprocessable Entity](https://tools.ietf.org/html/rfc2518#section-10.3)|Validation Error|[HTTPValidationError](#schemahttpvalidationerror)|

<aside class="success">
This operation does not require authentication
</aside>

## force_rebuild_embeddings_resolution_rebuild_embeddings_post

<a id="opIdforce_rebuild_embeddings_resolution_rebuild_embeddings_post"></a>

> Code samples

```shell
# You can also use wget
curl -X POST /resolution/rebuild-embeddings \
  -H 'Accept: application/json'

```

```http
POST /resolution/rebuild-embeddings HTTP/1.1

Accept: application/json

```

```javascript

const headers = {
  'Accept':'application/json'
};

fetch('/resolution/rebuild-embeddings',
{
  method: 'POST',

  headers: headers
})
.then(function(res) {
    return res.json();
}).then(function(body) {
    console.log(body);
});

```

```ruby
require 'rest-client'
require 'json'

headers = {
  'Accept' => 'application/json'
}

result = RestClient.post '/resolution/rebuild-embeddings',
  params: {
  }, headers: headers

p JSON.parse(result)

```

```python
import requests
headers = {
  'Accept': 'application/json'
}

r = requests.post('/resolution/rebuild-embeddings', headers = headers)

print(r.json())

```

```php
<?php

require 'vendor/autoload.php';

$headers = array(
    'Accept' => 'application/json',
);

$client = new \GuzzleHttp\Client();

// Define array of request body.
$request_body = array();

try {
    $response = $client->request('POST','/resolution/rebuild-embeddings', array(
        'headers' => $headers,
        'json' => $request_body,
       )
    );
    print_r($response->getBody()->getContents());
 }
 catch (\GuzzleHttp\Exception\BadResponseException $e) {
    // handle exception or api errors.
    print_r($e->getMessage());
 }

 // ...

```

```java
URL obj = new URL("/resolution/rebuild-embeddings");
HttpURLConnection con = (HttpURLConnection) obj.openConnection();
con.setRequestMethod("POST");
int responseCode = con.getResponseCode();
BufferedReader in = new BufferedReader(
    new InputStreamReader(con.getInputStream()));
String inputLine;
StringBuffer response = new StringBuffer();
while ((inputLine = in.readLine()) != null) {
    response.append(inputLine);
}
in.close();
System.out.println(response.toString());

```

```go
package main

import (
       "bytes"
       "net/http"
)

func main() {

    headers := map[string][]string{
        "Accept": []string{"application/json"},
    }

    data := bytes.NewBuffer([]byte{jsonReq})
    req, err := http.NewRequest("POST", "/resolution/rebuild-embeddings", data)
    req.Header = headers

    client := &http.Client{}
    resp, err := client.Do(req)
    // ...
}

```

`POST /resolution/rebuild-embeddings`

*Force Rebuild Embeddings*

Force full rebuild of embeddings cache (slow, prefer /feedback)

> Example responses

> 200 Response

```json
{
  "rebuilt": true,
  "records": 0,
  "embedding_dim": 0,
  "cache_file": "string",
  "cache_saved": true
}
```

<h3 id="force_rebuild_embeddings_resolution_rebuild_embeddings_post-responses">Responses</h3>

|Status|Meaning|Description|Schema|
|---|---|---|---|
|200|[OK](https://tools.ietf.org/html/rfc7231#section-6.3.1)|Successful Response|[EmbeddingsRebuildResponse](#schemaembeddingsrebuildresponse)|

<aside class="success">
This operation does not require authentication
</aside>

# Schemas

<h2 id="tocS_Data">Data</h2>
<!-- backwards compatibility -->
<a id="schemadata"></a>
<a id="schema_Data"></a>
<a id="tocSdata"></a>
<a id="tocsdata"></a>

```json
{
  "service_subcategory_name": "string",
  "team_name": "string",
  "service_name": "string",
  "last_team_id_name": "string",
  "title_anon": "string",
  "description_anon": "string",
  "public_log_anon": "string"
}

```

Data

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|service_subcategory_name|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|team_name|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|service_name|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|last_team_id_name|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|title_anon|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|description_anon|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|public_log_anon|any|false|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

<h2 id="tocS_EmbeddingsRebuildResponse">EmbeddingsRebuildResponse</h2>
<!-- backwards compatibility -->
<a id="schemaembeddingsrebuildresponse"></a>
<a id="schema_EmbeddingsRebuildResponse"></a>
<a id="tocSembeddingsrebuildresponse"></a>
<a id="tocsembeddingsrebuildresponse"></a>

```json
{
  "rebuilt": true,
  "records": 0,
  "embedding_dim": 0,
  "cache_file": "string",
  "cache_saved": true
}

```

EmbeddingsRebuildResponse

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|rebuilt|boolean|true|none|none|
|records|integer|true|none|none|
|embedding_dim|any|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|cache_file|any|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|cache_saved|boolean|true|none|none|

<h2 id="tocS_FeedbackRequest">FeedbackRequest</h2>
<!-- backwards compatibility -->
<a id="schemafeedbackrequest"></a>
<a id="schema_FeedbackRequest"></a>
<a id="tocSfeedbackrequest"></a>
<a id="tocsfeedbackrequest"></a>

```json
{
  "ticket_title": "string",
  "ticket_description": "string",
  "edited_response": "string",
  "predicted_team": "string",
  "predicted_classification": "string",
  "service_name": "string",
  "service_subcategory": "string"
}

```

FeedbackRequest

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|ticket_title|string|true|none|Original ticket title|
|ticket_description|string|true|none|Original ticket description|
|edited_response|string|true|none|User-approved/edited response|
|predicted_team|any|false|none|Team assignment|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|predicted_classification|any|false|none|Ticket type|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|service_name|any|false|none|Service category|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|service_subcategory|any|false|none|Service subcategory|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

<h2 id="tocS_FeedbackResponse">FeedbackResponse</h2>
<!-- backwards compatibility -->
<a id="schemafeedbackresponse"></a>
<a id="schema_FeedbackResponse"></a>
<a id="tocSfeedbackresponse"></a>
<a id="tocsfeedbackresponse"></a>

```json
{
  "success": true,
  "message": "string",
  "ticket_ref": "string",
  "new_kb_size": 0,
  "embedding_added_incrementally": true,
  "embedding_invalidated": true
}

```

FeedbackResponse

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|success|boolean|true|none|none|
|message|string|true|none|none|
|ticket_ref|any|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|new_kb_size|any|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|embedding_added_incrementally|boolean|true|none|none|
|embedding_invalidated|boolean|true|none|none|

<h2 id="tocS_HTTPValidationError">HTTPValidationError</h2>
<!-- backwards compatibility -->
<a id="schemahttpvalidationerror"></a>
<a id="schema_HTTPValidationError"></a>
<a id="tocShttpvalidationerror"></a>
<a id="tocshttpvalidationerror"></a>

```json
{
  "detail": [
    {
      "loc": [
        "string"
      ],
      "msg": "string",
      "type": "string"
    }
  ]
}

```

HTTPValidationError

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|detail|[[ValidationError](#schemavalidationerror)]|false|none|none|

<h2 id="tocS_LabelRequest">LabelRequest</h2>
<!-- backwards compatibility -->
<a id="schemalabelrequest"></a>
<a id="schema_LabelRequest"></a>
<a id="tocSlabelrequest"></a>
<a id="tocslabelrequest"></a>

```json
{
  "query_idx": [
    0
  ],
  "labels": [
    "string"
  ]
}

```

LabelRequest

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|query_idx|[anyOf]|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|labels|[anyOf]|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

<h2 id="tocS_NewInstance">NewInstance</h2>
<!-- backwards compatibility -->
<a id="schemanewinstance"></a>
<a id="schema_NewInstance"></a>
<a id="tocSnewinstance"></a>
<a id="tocsnewinstance"></a>

```json
{
  "model_name": "string",
  "qs_strategy": "string",
  "class_list": [
    0
  ],
  "train_data_path": "string",
  "test_data_path": "string"
}

```

NewInstance

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|model_name|string|true|none|none|
|qs_strategy|string|true|none|none|
|class_list|[anyOf]|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|train_data_path|string|true|none|none|
|test_data_path|string|true|none|none|

<h2 id="tocS_ResolutionRequest">ResolutionRequest</h2>
<!-- backwards compatibility -->
<a id="schemaresolutionrequest"></a>
<a id="schema_ResolutionRequest"></a>
<a id="tocSresolutionrequest"></a>
<a id="tocsresolutionrequest"></a>

```json
{
  "ticket_title": "string",
  "ticket_description": "string",
  "service_category": "string",
  "service_subcategory": "string",
  "top_k": 3,
  "force_rebuild": false
}

```

ResolutionRequest

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|ticket_title|any|false|none|Title of the ticket|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|ticket_description|any|false|none|Description of the ticket|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|service_category|any|false|none|Service category if available|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|service_subcategory|any|false|none|Service subcategory if available|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|null|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|top_k|integer|false|none|Number of similar tickets to retrieve|
|force_rebuild|boolean|false|none|Force rebuild of embeddings cache|

<h2 id="tocS_ResolutionResponse">ResolutionResponse</h2>
<!-- backwards compatibility -->
<a id="schemaresolutionresponse"></a>
<a id="schema_ResolutionResponse"></a>
<a id="tocSresolutionresponse"></a>
<a id="tocsresolutionresponse"></a>

```json
{
  "classification": "string",
  "predicted_team": "string",
  "team_confidence": 0,
  "response": "string",
  "similar_replies": [
    {}
  ],
  "retrieval_k": 0
}

```

ResolutionResponse

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|classification|string|true|none|Classified ticket type (e.g., vpn_request, onboarding)|
|predicted_team|string|true|none|Team assigned to handle the ticket|
|team_confidence|number|true|none|Confidence score for team prediction|
|response|string|true|none|Generated first reply to the ticket|
|similar_replies|[object]|true|none|Similar historical tickets|
|retrieval_k|integer|true|none|Number of similar tickets retrieved|

<h2 id="tocS_ValidationError">ValidationError</h2>
<!-- backwards compatibility -->
<a id="schemavalidationerror"></a>
<a id="schema_ValidationError"></a>
<a id="tocSvalidationerror"></a>
<a id="tocsvalidationerror"></a>

```json
{
  "loc": [
    "string"
  ],
  "msg": "string",
  "type": "string"
}

```

ValidationError

### Properties

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|loc|[anyOf]|true|none|none|

anyOf

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|string|false|none|none|

or

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|» *anonymous*|integer|false|none|none|

continued

|Name|Type|Required|Restrictions|Description|
|---|---|---|---|---|
|msg|string|true|none|none|
|type|string|true|none|none|

