# :robot: Backend API Documentation

Below is everything present in the API for the backend of this pastebin service.

## Creating a paste

Pastes are created by sending a `POST` request to the `/create/` endpoint.

Its paste ID and removal link, after creation, are also included in the resulting JSON.

### Demonstration
```py
import requests

requests.post(
    ".../create/",
    json = {
        "files": [
            ["test.py", 'print("Hello world!")']
        ]
    }
)
```

> :memo: **Note:** You can also include a `"keep_for"` key with a number for the amount of days you want the paste kept for.

### HTTP Status Codes

|Code|Explanation|
|:-:|:-|
|`400`|Bad request; the data sent did not match the expected schema.|
|`403`|The database has reached its maximum allowed entries and is not allowing any more pastes to be created.
|`422`|Combined file size exceeds the cap (shown in error message).|
|`200`|The operation executed successfully.|


## Deleting a paste

Pastes are deleted by sending a `DELETE` request to the `/delete/` endpoint, attaching the relevant paste ID to the end of the link.

This allows the operation to be performed from a hyperlink, as it's just a URL.

### Demonstration
```py
import requests

requests.delete(".../delete/8xV3y38NbY")
```

### HTTP Status Codes

|Code|Explanation|
|:-:|:-|
|`404`|No paste was found with the given ID.|
|`200`|The operation executed successfully.|


## Getting a paste

Pastes are retrieved by sending a `GET` request to the `/get/` endpoint, attaching the relevant paste ID to the end of the link.

### Demonstration

Code:
```py
import requests

requests.get(".../get/8xV3y38NbY")
```

### HTTP Status Codes

|Code|Explanation|
|:-:|:-|
|`400`|Bad request; the data sent did not match the expected schema.|
|`404`|No paste was found with the given ID.|
|`200`|The operation executed successfully.|


## Getting a (raw) paste

Raw pastes are retrieved by sending a `GET` request to the `/get/raw/` endpoint, in one of two ways.

The first is attaching just the relevant paste ID to the end. This will retrieve _all_ files in that paste, adding the filename as a header and separating them by the following: `"\n\n***\n\n"`:
```yml
[test.py]
print("Hello world!")

***

[???]
print("He who shall not be named.")
```

The second is similar to the first, but it's further extended by an index. This will return just one file in plain text, the filename in square brackets preceding the code.

> :memo: **Note:** the "index" I mentioned is its position in the paste order. This is 1-indexed for human readability.

### Demonstration 1

Code:
```py
import requests

requests.get(".../get/raw/8xV3y38NbY")
```

### Demonstration 2

Code:
```py
import requests

requests.get(".../get/raw/8xV3y38NbY/1")
```

This gets the first file in the multi-file paste.

### HTTP Status Codes

The codes for this endpoint are returned in plain text and contain specific explanations, meaning there is no need for a table here.


## Updating a paste

Pastes are retrieved by sending a `PUT` request to the `/update/` endpoint, attaching the relevant paste ID to the end of the link.

### Demonstration

Code:
```py
import requests

requests.put(".../update/8xV3y38NbY")
```

### HTTP Status Codes

|Code|Explanation|
|:-:|:-|
|`400`|Bad request; the data sent did not match the expected schema.|
|`404`|No paste was found with the given ID.|
|`200`|The operation executed successfully.|