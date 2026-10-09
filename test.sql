DROP VIEW IF EXISTS person_with_age;
/* ▶ ✓
DROP VIEW
*/
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

-- age depends on today's date, so it can't be stored; a view calculates it on every read
CREATE VIEW person_with_age AS
SELECT *, date_part('year', age(date_of_birth))::int AS age
FROM person;
/* ▶ ✓
CREATE VIEW
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

SELECT * FROM person_with_age;
/* ▶ ✓
 id |     name     |   address   | date_of_birth | age 
----+--------------+-------------+---------------+-----
  1 | Jahidun Nur  | 123 Main St | 1999-02-01    |  27
  2 | John Doe     | 456 Elm St  | 1985-07-15    |  41
  3 | Harry potter | 789 Oak St  | 2000-12-31    |  25
(3 rows)
*/

SELECT id, date_of_birth, age FROM person_with_age;
/* ▶ ✓
 id | date_of_birth | age 
----+---------------+-----
  1 | 1999-02-01    |  27
  2 | 1985-07-15    |  41
  3 | 2000-12-31    |  25
(3 rows)
*/

SELECT * FROM person_with_age
ORDER BY age ASC;
/* ▶ ✓
 id |     name     |   address   | date_of_birth | age 
----+--------------+-------------+---------------+-----
  3 | Harry potter | 789 Oak St  | 2000-12-31    |  25
  1 | Jahidun Nur  | 123 Main St | 1999-02-01    |  27
  2 | John Doe     | 456 Elm St  | 1985-07-15    |  41
(3 rows)
*/