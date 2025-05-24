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

ALTER DATABASE eco OWNER TO postgres;

\connect eco

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
    hpipe integer,
    dpipe integer,
    substances character varying,
    x character varying,
    y character varying,
    blowout double precision,
    dxy integer,
    dz integer,
    min_x integer,
    max_x integer,
    days integer
);


ALTER TABLE public.isa OWNER TO postgres;

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


ALTER TABLE public.isa_id_seq OWNER TO postgres;

--
-- Name: isa_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.isa_id_seq OWNED BY public.isa.id;


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
    latitude double precision,
    longitude double precision,
    weight integer
);


ALTER TABLE public.sensors OWNER TO postgres;

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


ALTER TABLE public.substance_id_sub_seq OWNER TO postgres;

--
-- Name: substance_id_sub_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.substance_id_sub_seq OWNED BY public.substance.id_sub;


--
-- Name: isa id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.isa ALTER COLUMN id SET DEFAULT nextval('public.isa_id_seq'::regclass);


--
-- Name: substance id_sub; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.substance ALTER COLUMN id_sub SET DEFAULT nextval('public.substance_id_sub_seq'::regclass);


--
-- Data for Name: blt; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.blt (longitude, latitude, weight) FROM stdin;
57.916325	56.19061	\N
57.88205	56.072586	\N
57.893261	56.140047	10
57.943622	56.183463	\N
57.91596	56.207855	\N
57.944087	56.139014	\N
57.953116	56.095568	\N
57.916325	56.207855	\N
\.


--
-- Data for Name: btlk; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.btlk (latitude, longitude, weight) FROM stdin;
57.908419163034765	56.13620107049552	50
\.


--
-- Data for Name: factory; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.factory (latitude, longitude) FROM stdin;
57.908419163034765	56.13620107049552
\.


--
-- Data for Name: isa; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.isa (id, nameisa, hpipe, dpipe, substances, x, y, blowout, dxy, dz, min_x, max_x, days) FROM stdin;
2	5	10	12	jghj	5	\N	6	\N	\N	\N	\N	\N
1	test	10	12	jghj	5	\N	6	\N	\N	3	\N	\N
\.


--
-- Data for Name: pipes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pipes (latitude, longitude, weight) FROM stdin;
57.92526312384498	56.12444799478024	100
57.908419163034765	56.13620107049552	110
57.92539929836258	56.14581121563227	110
57.90976279175196	56.121160444863634	110
57.91672183570379	56.119026324875094	110
\.


--
-- Data for Name: sensors; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.sensors (latitude, longitude, weight) FROM stdin;
57.916325	56.207855	\N
57.91596	56.072586	\N
57.953116	56.140047	\N
57.88205	56.139014	\N
57.943622	56.090029	\N
57.89237	56.183463	\N
57.944087	56.19061	\N
57.893261	56.095568	\N
\.


--
-- Data for Name: substance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.substance (id_sub, namesubstance, pdk, nu, ro, m_s, dry_size) FROM stdin;
1	pm25	20	11.5	7	67	5
\.


--
-- Name: isa_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.isa_id_seq', 2, true);


--
-- Name: substance_id_sub_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.substance_id_sub_seq', 1, true);


--
-- Name: isa isa_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.isa
    ADD CONSTRAINT isa_pk PRIMARY KEY (id);


--
-- Name: substance substance_pk; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.substance
    ADD CONSTRAINT substance_pk PRIMARY KEY (id_sub);


--
-- PostgreSQL database dump complete
--

