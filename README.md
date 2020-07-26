# private-tree-hole
重复造轮子。

计划重构。会用Vue重构一个Repo出来。

## 也许你需要自己用
创建```db_export.py```
里面填写
```py
USERNAME = 'treehole'
PASSWORD = 'rDbNGdnyasnPjdkb'
HOST = 'lakejason0.ml'
PORT = 3306
DATABASE = 'treehole'
```
## API

### `/api/thread/<id>`

#### 方法

使用`GET`或`POST`。

#### 参数

所有传入参数都应传入`action`和`data`。

##### `action`

先实现了`get`和`reply`。

###### `get`

好像就没了.jpg

###### `reply`

`data`内部应该包含`username`和`content`。任何`content`为空的请求都会被告知`400`错误。

后端内部，`data`内部还会包含`time`，但处理时会覆写前端所提供的`time`参数。

### `/api/thread`

#### 方法

使用`POST`。

#### 参数

所有传入参数都应传入`action`和`data`。

##### `action`

先实现了`create`，`query`尚未实现。

###### `create`

`data`内部应该包含`username`、`title`、`content`。任何`title`和`content`同时为空的请求都会被告知`400`错误。

后端内部，`data`内部还会包含`time`和`floor`，同样会被覆写。

### `/api/public`

#### 方法

随意。

### 返回

所有API返回的JSON都会包含以下字段：

#### `code`

返回的状态码。遵守HTTP协议。

#### `data`

返回的数据。请查看你所需的API。

#### `toast`

返回的Toast，一个列表。若存在，应该将里面的内容提取出来展示为Toast。

##### `code`

返回的状态码。遵守HTTP协议。

##### `message`

返回的信息。为硬编码的英文。

##### `identifier`

返回消息的标识符。用于i18n。