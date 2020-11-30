DROP TABLE if EXISTS users;

DROP TABLE if EXISTS equations;

CREATE TABLE users (
	username text NOT NULL UNIQUE,
	pass text
);

CREATE TABLE equations (
	title text UNIQUE,
	def text UNIQUE,
	user integer
);

INSERT INTO equations VALUES("The Placeholder Theorum","y=mx+c", -1);
INSERT INTO equations VALUES("The Sample Quandary","x^2-1", -1);

INSERT INTO equations VALUES("The Custom Theorum","y=mx+c+q", 0);
INSERT INTO equations VALUES("The Qustom Quandary","x^2-1+q", 0);