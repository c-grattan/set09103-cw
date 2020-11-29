DROP TABLE if EXISTS users;

CREATE TABLE users (
	username text NOT NULL UNIQUE,
	pass text
);