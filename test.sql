DROP TABLE IF EXISTS person;
/* ▶ ✓
DROP TABLE
*/

CREATE TABLE person (
    id int,
    name varchar(80),
    address varchar(255),
    date_of_birth date
);
/* ▶ ✓
CREATE TABLE
*/

INSERT INTO person (id,name,address,date_of_birth)
VALUES (1,'Jahidun Nur','123 Main St','1999-02-01');
/* ▶ ✓
INSERT 0 1
*/

INSERT INTO person (id,name,address,date_of_birth)
VALUES (2,'John Doe','456 Elm St','1985-07-15');
/* ▶ ✓
INSERT 0 1
*/

INSERT INTO person (id,name,address,date_of_birth)
VALUES (3,'Harry potter', '789 Oak St','2000-12-31');
/* ▶ ✓
INSERT 0 1
*/

SELECT * FROM person;
/* ▶ ✓
 id |     name     |   address   | date_of_birth 
----+--------------+-------------+---------------
  1 | Jahidun Nur  | 123 Main St | 1999-02-01
  2 | John Doe     | 456 Elm St  | 1985-07-15
  3 | Harry potter | 789 Oak St  | 2000-12-31
(3 rows)
*/

SELECT id, date_of_birth FROM person;
/* ▶ ✓
 id | date_of_birth 
----+---------------
  1 | 1999-02-01
  2 | 1985-07-15
  3 | 2000-12-31
(3 rows)
*/