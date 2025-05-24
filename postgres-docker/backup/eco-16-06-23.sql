--
-- PostgreSQL database dump
--

-- Dumped from database version 12.20 (Debian 12.20-1.pgdg120+1)
-- Dumped by pg_dump version 12.20 (Debian 12.20-1.pgdg120+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET default_tablespace = '';
SET default_table_access_method = heap;

ALTER DATABASE eco OWNER TO postgres;

\connect eco


--
-- Name: blt; Type: TABLE; Schema: public; Owner: postgres
--
CREATE TABLE public.blt (
    longitude double precision,
    latitude double precision,
    weight integer
);


ALTER TABLE public.blt OWNER TO postgres;

--
-- Name: btlk; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.btlk (
    latitude double precision,
    longitude double precision,
    weight integer
);


ALTER TABLE public.btlk OWNER TO postgres;

--
-- Name: factory; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.factory (
    latitude double precision,
    longitude double precision
);


ALTER TABLE public.factory OWNER TO postgres;

--
-- Name: isa; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.isa (
    id integer NOT NULL,
    nameisa character varying,
    hpipe double precision,
    dpipe double precision,
    substances character varying,
    x character varying,
    y character varying,
    blowout double precision,
    days integer,
    temperature double precision,
    exit_velocity double precision,
    emission_rate double precision
);


ALTER TABLE public.isa OWNER TO postgres;

--
-- Name: COLUMN isa.exit_velocity; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.isa.exit_velocity IS 'Скорость выхода';


--
-- Name: isa_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.isa_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.isa_id_seq OWNER TO postgres;

--
-- Name: isa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.isa_id_seq OWNED BY public.isa.id;


--
-- Name: other; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.other (
    id_other integer NOT NULL,
    size_h integer,
    size_w integer,
    longitude_o character varying,
    latitude_o character varying,
    step double precision
);


ALTER TABLE public.other OWNER TO postgres;

--
-- Name: other_id_other_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.other_id_other_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.other_id_other_seq OWNER TO postgres;

--
-- Name: other_id_other_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.other_id_other_seq OWNED BY public.other.id_other;


--
-- Name: pipes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pipes (
    latitude double precision,
    longitude double precision,
    weight integer
);


ALTER TABLE public.pipes OWNER TO postgres;

--
-- Name: sensors; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sensors (
    latitude character varying,
    longitude character varying,
    substances character varying,
    sheight double precision,
    namesensor character varying,
    id integer NOT NULL
);


ALTER TABLE public.sensors OWNER TO postgres;

--
-- Name: sensors_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sensors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sensors_id_seq OWNER TO postgres;

--
-- Name: sensors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sensors_id_seq OWNED BY public.sensors.id;


--
-- Name: substance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.substance (
    id_sub integer NOT NULL,
    namesubstance character varying,
    pdk double precision,
    nu double precision,
    ro double precision,
    m_s double precision,
    dry_size double precision
);


ALTER TABLE public.substance OWNER TO postgres;

--
-- Name: substance_id_sub_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.substance_id_sub_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.substance_id_sub_seq OWNER TO postgres;

--
-- Name: substance_id_sub_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.substance_id_sub_seq OWNED BY public.substance.id_sub;


--
-- Name: isa id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.isa ALTER COLUMN id SET DEFAULT nextval('public.isa_id_seq'::regclass);


--
-- Name: other id_other; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.other ALTER COLUMN id_other SET DEFAULT nextval('public.other_id_other_seq'::regclass);


--
-- Name: sensors id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sensors ALTER COLUMN id SET DEFAULT nextval('public.sensors_id_seq'::regclass);


--
-- Name: substance id_sub; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.substance ALTER COLUMN id_sub SET DEFAULT nextval('public.substance_id_sub_seq'::regclass);


--
-- Data for Name: blt; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.916325, 56.19061, NULL);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.88205, 56.072586, NULL);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.893261, 56.140047, 10);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.943622, 56.183463, NULL);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.91596, 56.207855, NULL);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.944087, 56.139014, NULL);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.953116, 56.095568, NULL);
INSERT INTO public.blt (longitude, latitude, weight) VALUES (57.916325, 56.207855, NULL);


--
-- Data for Name: btlk; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.btlk (latitude, longitude, weight) VALUES (57.908419163034765, 56.13620107049552, 50);


--
-- Data for Name: factory; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.factory (latitude, longitude) VALUES (57.908419163034765, 56.13620107049552);


--
-- Data for Name: isa; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (4, '118', 100, 4.2, NULL, '52.526192183', '39.633721625', NULL, NULL, 70, 8.06, 12.5136);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (1, '2', 100, 1.82, 'so2', '52.553939546', '39.565789939', 6, NULL, 90, 14.95, 1.62409);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (13, '207', 25.7, 6.4, NULL, '52.561467104', '39.601438225', NULL, NULL, 100, 0.92, 0.130676);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (12, '4', 60, 5, NULL, '52.526947659', '39.631084757', NULL, NULL, 70, 16.98, 0.0738);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (11, '42', 60, 6, NULL, '52.527304092', '39.642076555', NULL, NULL, 60, 13.75, 0.04591);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (3, '304', 18.5, 0.45, NULL, '52.558375462', '39.594095627', NULL, NULL, 27, 15.7, 0.042865);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (14, '310', 18.5, 0.45, NULL, '52.557521629', '39.592577154', NULL, NULL, 27, 15.7, 0.042862);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (15, '27', 60, 5.5, NULL, '52.553657445', '39.591826239', NULL, NULL, 80, 11.69, 0.033872);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (16, '48', 31, 4.22, NULL, '52.557279401', '39.598430627', NULL, NULL, 50, 13.94, 0.02151);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (17, '110', 28.7, 2.69, NULL, '52.557279401', '39.598430627', NULL, NULL, 65, 15.1, 0.021521);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (18, '111', 28.7, 2.69, NULL, '52.555077599', '39.595570668', NULL, NULL, 65, 15.1, 0.014969);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (2, '10', 100, 4.2, 'H2S', '52.526605454', '39.63410498', 6, NULL, 70, 8.06, 12.5748);
INSERT INTO public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, days, temperature, exit_velocity, emission_rate) VALUES (19, 'Новый ИЗА', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);


--
-- Data for Name: other; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.other (id_other, size_h, size_w, longitude_o, latitude_o, step) VALUES (1, 10, 10, '1222', '1222', 10);


--
-- Data for Name: pipes; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.pipes (latitude, longitude, weight) VALUES (57.92526312384498, 56.12444799478024, 100);
INSERT INTO public.pipes (latitude, longitude, weight) VALUES (57.908419163034765, 56.13620107049552, 110);
INSERT INTO public.pipes (latitude, longitude, weight) VALUES (57.92539929836258, 56.14581121563227, 110);
INSERT INTO public.pipes (latitude, longitude, weight) VALUES (57.90976279175196, 56.121160444863634, 110);
INSERT INTO public.pipes (latitude, longitude, weight) VALUES (57.91672183570379, 56.119026324875094, 110);


--
-- Data for Name: sensors; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.607616', '39.601979', 'H₂S', 2, 'Липецк пост №11', 1);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.603116', '39.51394', 'H₂S', 2, 'Липецк пост №12', 2);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.619456', '39.553595', 'H₂S', 2, 'Липецк пост №2', 3);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.580566', '39.621148', 'H₂S', 2, 'Липецк пост №3', 4);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.537643', '39.582062', 'H₂S', 2, 'Липецк пост №4', 5);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.639713', '39.65912', 'H₂S', 2, 'Липецк пост №6', 6);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.590573', '39.530589', 'H₂S', 2, 'Липецк пост №8', 7);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.527775', '39.676104', 'H₂S', 1.99, 'ул. Балашовское лесничество', 8);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.577223', '39.598655', 'H₂S', 2, 'ул. Гастелло', 9);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.539149', '39.579962', 'H₂S', 2, 'Дворец культуры', 10);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.552504', '39.561566', 'H₂S', 2, 'СТ Дружба', 11);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.574359', '39.669188', 'H₂S', 2, 'ул. Зои Космодемьянской, 46/1', 12);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.53023', '39.596675', 'H₂S', 2, 'ул. Спартака', 13);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.565069', '39.716292', 'H₂S', 2, 'ул. Тепличная, 40/1', 14);
INSERT INTO public.sensors (latitude, longitude, substances, sheight, namesensor, id) VALUES ('52.573889', '39.629935', 'H₂S', 2, 'ул. Ферросплавная', 15);


--
-- Data for Name: substance; Type: TABLE DATA; Schema: public; Owner: postgres
--

INSERT INTO public.substance (id_sub, namesubstance, pdk, nu, ro, m_s, dry_size) VALUES (1, 'pm25', 20, 11.5, 7, 67, 5);
INSERT INTO public.substance (id_sub, namesubstance, pdk, nu, ro, m_s, dry_size) VALUES (5, 'Новое вещество', NULL, NULL, NULL, NULL, NULL);


--
-- Name: isa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.isa_id_seq', 19, true);


--
-- Name: other_id_other_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.other_id_other_seq', 1, true);


--
-- Name: sensors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.sensors_id_seq', 15, true);


--
-- Name: substance_id_sub_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.substance_id_sub_seq', 5, true);


--
-- Name: isa isa_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.isa
    ADD CONSTRAINT isa_pk PRIMARY KEY (id);


--
-- Name: other other_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.other
    ADD CONSTRAINT other_pk PRIMARY KEY (id_other);


--
-- Name: sensors sensors_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sensors
    ADD CONSTRAINT sensors_pk PRIMARY KEY (id);


--
-- Name: substance substance_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.substance
    ADD CONSTRAINT substance_pk PRIMARY KEY (id_sub);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

