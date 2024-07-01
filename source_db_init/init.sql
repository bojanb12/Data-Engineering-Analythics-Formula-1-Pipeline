
CREATE TABLE "sprintDim" (
  "raceId" int,
  "driverId" int,
  "sprint_date" date,
  "sprint_time" time
);

CREATE TABLE "driverDim" (
  "driverId" integer PRIMARY KEY,
  "driverRef" varchar,
  "forename" varchar,
  "surname" varchar,
  "dob" date,
  "nationality" varchar,
  "code" varchar,
  "number" int,
  "url" varchar
);

CREATE TABLE "constructorDim" (
  "constructorId" integer PRIMARY KEY,
  "constructorRef" varchar,
  "name" varchar,
  "nationality_constructors" varchar,
  "url_constructors" varchar
);

CREATE TABLE "raceDim" (
  "raceId" integer PRIMARY KEY,
  "circuitId" int,
  "name_x" varchar,
  "date" date,
  "year" int,
  "round" int,
  "time_races" time,
  "url_x" varchar
);

CREATE TABLE "circuitDim" (
  "circuitId" integer PRIMARY KEY,
  "name_y" varchar,
  "circuitRef" varchar,
  "location" varchar,
  "country" varchar,
  "lat" float,
  "lng" float,
  "alt" float,
  "url_y" varchar
);

CREATE TABLE "raceStatusDim" (
  "statusId" integer PRIMARY KEY,
  "status" varchar
);

CREATE TABLE "driverStandingsDim" (
  "driverStandingsId" int PRIMARY KEY,
  "driverId" int,
  "position_driverstandings" int,
  "points_driverstandings" float,
  "wins" int
);

CREATE TABLE "constructorStandingsDim" (
  "constructorStandingsId" int PRIMARY KEY,
  "constructorId" int,
  "position_constructorstandings" int,
  "wins_constructorstandings" int,
  "points_constructorstandings" float
);

CREATE TABLE "pitStopsDim" (
  "raceId" int,
  "driverId" int,
  "stop" int,
  "lap_pitstops" int,
  "time_pitstops" time,
  "duration" float
);

CREATE TABLE "lapsDim" (
  "raceId" int,
  "driverId" int,
  "lap" int,
  "time_laptimes" time,
  "milliseconds_laptimes" float,
  "position_laptimes" int
);

CREATE TABLE "qualificationsDim" (
  "raceId" int,
  "driverId" int,
  "quali_time" time,
  "quali_date" date
);

CREATE TABLE "freePracticeDim" (
  "raceId" int,
  "fp1_date" date,
  "fp2_date" date,
  "fp3_date" date,
  "fp1_time" time,
  "fp3_time" time,
  "fp2_time" time
);

CREATE TABLE "raceResultsFact" (
  "resultId" int PRIMARY KEY,
  "raceId" int,
  "constructorId" int,
  "driverId" int,
  "constructorStandingsId" int,
  "driverStandingsId" int,
  "statusId" int,
  "positionOrder" int,
  "points" float,
  "laps" int,
  "grid" int,
  "fastestLapTime" varchar,
  "fastestLapSpeed" float,
  "time" varchar,
  "fastestLap" int
);

ALTER TABLE "raceResultsFact" ADD FOREIGN KEY ("raceId") REFERENCES "raceDim" ("raceId");

ALTER TABLE "raceResultsFact" ADD FOREIGN KEY ("constructorId") REFERENCES "constructorDim" ("constructorId");

ALTER TABLE "raceResultsFact" ADD FOREIGN KEY ("driverId") REFERENCES "driverDim" ("driverId");

ALTER TABLE "raceResultsFact" ADD FOREIGN KEY ("constructorStandingsId") REFERENCES "constructorStandingsDim" ("constructorStandingsId");

ALTER TABLE "raceResultsFact" ADD FOREIGN KEY ("driverStandingsId") REFERENCES "driverStandingsDim" ("driverStandingsId");

ALTER TABLE "raceDim" ADD FOREIGN KEY ("circuitId") REFERENCES "circuitDim" ("circuitId");

ALTER TABLE "raceResultsFact" ADD FOREIGN KEY ("statusId") REFERENCES "raceStatusDim" ("statusId");

ALTER TABLE "pitStopsDim" ADD FOREIGN KEY ("raceId") REFERENCES "raceResultsFact" ("raceId");

ALTER TABLE "pitStopsDim" ADD FOREIGN KEY ("driverId") REFERENCES "raceResultsFact" ("driverId");

ALTER TABLE "lapsDim" ADD FOREIGN KEY ("raceId") REFERENCES "raceResultsFact" ("raceId");

ALTER TABLE "lapsDim" ADD FOREIGN KEY ("driverId") REFERENCES "raceResultsFact" ("driverId");

ALTER TABLE "qualificationsDim" ADD FOREIGN KEY ("raceId") REFERENCES "raceResultsFact" ("raceId");

ALTER TABLE "qualificationsDim" ADD FOREIGN KEY ("driverId") REFERENCES "raceResultsFact" ("driverId");

ALTER TABLE "freePracticeDim" ADD FOREIGN KEY ("raceId") REFERENCES "raceResultsFact" ("raceId");

ALTER TABLE "sprintDim" ADD FOREIGN KEY ("raceId") REFERENCES "raceResultsFact" ("raceId");

ALTER TABLE "sprintDim" ADD FOREIGN KEY ("driverId") REFERENCES "raceResultsFact" ("driverId");

ALTER TABLE "driverStandingsDim" ADD FOREIGN KEY ("driverId") REFERENCES "raceResultsFact" ("driverId");

ALTER TABLE "constructorStandingsDim" ADD FOREIGN KEY ("constructorId") REFERENCES "constructorDim" ("constructorId");
