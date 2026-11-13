# 启动本机 Qdrant

知识分块向量放在本机 Qdrant，不随 `docker compose` 一起启动。不要执行仓库里的整份 `docker compose up`，那会拉起 Milvus、etcd 和 MinIO。

Qdrant 服务端是 Apache 2.0，使用官方镜像自建时没有许可费。下面这条命令只启动本机容器，地址是 `http://127.0.0.1:6333`。

```powershell
docker run -d --name opspilot-qdrant -p 6333:6333 -v qdrant_storage:/qdrant/storage qdrant/qdrant
```

后端默认读取环境变量 `QDRANT_URL`，未设置时使用 `http://127.0.0.1:6333`。集合名是 `opspilot_chunks`，距离是余弦，维度与当前嵌入模型一致。默认嵌入 `local-hash-256` 是 256 维。集合在第一次写入分块时创建，不导入旧的 `knowledge_chunks`。

Qdrant 没启动时，后端仍可登录和保存业务数据。知识检索会返回明确错误：接口状态码 503，对话里的检索则跳过并继续回答。

查看容器是否在跑：

```powershell
docker ps --filter name=opspilot-qdrant
```

停止并保留数据：

```powershell
docker stop opspilot-qdrant
```
