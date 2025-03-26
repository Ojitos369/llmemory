/*
dr run -d --name llmemory-db \
    -e POSTGRES_PASSWORD=Contra12345$ \
    -e POSTGRES_DB=llmemory \
    -e PGDATA=/var/lib/postgresql/data/pgdata \
    -e POSTGRES_USER=llmemory \
    -e TZ=America/Mexico_City \
    --mount src=llmemory,dst=/var/lib/postgresql/data \
    -p 5436:5432 \
    --shm-size=1024m \
    postgres

dr exec -it llmemory-db psql -U llmemory -d llmemory
*/

-- id_mensaje, fecha_mensaje, tipo_usuario, pensamiento, mensaje

CREATE TABLE chat_unico (
    id_chat VARCHAR(50) NOT NULL,
    mensaje TEXT,
    
    CONSTRAINT pk_chuni PRIMARY KEY (id_chat)
);

CREATE TABLE mensajes (
    id_mensaje VARCHAR(50) NOT NULL,
    fecha_mensaje TIMESTAMP NOT NULL,
    tipo_usuario VARCHAR(50) NOT NULL,
    pensamiento VARCHAR(50),
    mensaje VARCHAR(50) NOT NULL,
    CONSTRAINT pk_mensajes PRIMARY KEY (id_mensaje)
);

-- id_union, mensaje_id, palabra
CREATE TABLE uniones (
    id_union VARCHAR(50) NOT NULL,
    mensaje_id VARCHAR(50) NOT NULL,
    palabra VARCHAR(50) NOT NULL,
    CONSTRAINT pk_uniones PRIMARY KEY (id_union),
    CONSTRAINT fk_mensaje_id FOREIGN KEY (mensaje_id) REFERENCES mensajes(id_mensaje)
);