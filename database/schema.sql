--
-- PostgreSQL database dump
--

\restrict rYqRwnu7TM5dDlFgCWnHPVPEiDrZJiIWbuQUcGiM5sQkRqtFaXCq9EvhGzcb7OC

-- Dumped from database version 18.6
-- Dumped by pg_dump version 18.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: business_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.business_rules (
    rule_id character varying(20) NOT NULL,
    rule_name character varying(150),
    rule_text text,
    department character varying(100)
);


--
-- Name: company_master; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.company_master (
    company_id character varying(20) NOT NULL,
    company_name character varying(150),
    legal_name character varying(200),
    registration_no character varying(100),
    industry character varying(100),
    business_type character varying(100),
    headquarters character varying(150),
    fiscal_year character varying(20),
    timezone character varying(50),
    currency character varying(10),
    tax_configuration text
);


--
-- Name: customers; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.customers (
    customer_id character varying(20) NOT NULL,
    company_name character varying(150),
    contact_person character varying(100),
    email character varying(150),
    phone character varying(30),
    address text,
    industry character varying(100),
    account_owner_id character varying(20),
    sales_representative_id character varying(20),
    customer_status character varying(50),
    contract_id character varying(50),
    products_services text,
    lifetime_value_inr numeric(15,2)
);


--
-- Name: documents; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.documents (
    document_id character varying(20) NOT NULL,
    document_type character varying(100),
    title character varying(255),
    entity_id character varying(50),
    created_date date,
    file_name character varying(255),
    access_level character varying(50)
);


--
-- Name: emails; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.emails (
    message_id character varying(20) NOT NULL,
    sender character varying(150),
    recipient character varying(150),
    "timestamp" timestamp without time zone,
    subject character varying(255),
    body text,
    thread_id character varying(50),
    source character varying(100),
    permissions character varying(100)
);


--
-- Name: employees; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.employees (
    employee_id character varying(20) NOT NULL,
    name character varying(100),
    work_email character varying(150),
    department character varying(100),
    team character varying(100),
    job_role character varying(100),
    manager_id character varying(20),
    location character varying(100),
    joining_date date,
    employment_status character varying(50),
    assigned_project character varying(100),
    responsibilities text,
    approval_authority_inr numeric(15,2)
);


--
-- Name: events; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.events (
    event_id character varying(20) NOT NULL,
    event_type character varying(100),
    entity_id character varying(50),
    "timestamp" timestamp without time zone,
    actor character varying(100),
    old_value text,
    new_value text,
    source character varying(100),
    metadata text
);


--
-- Name: expenses; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.expenses (
    expense_id character varying(20) NOT NULL,
    cost_center character varying(50),
    expense_date date,
    category character varying(100),
    amount_inr numeric(15,2),
    approved_by character varying(100)
);


--
-- Name: ingestion_test_business_rules; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.ingestion_test_business_rules (
    rule_id character varying(50) NOT NULL,
    rule_name character varying(255) NOT NULL,
    rule_text text NOT NULL,
    department character varying(100)
);


--
-- Name: payments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.payments (
    payment_id character varying(20) NOT NULL,
    invoice_id character varying(20),
    payment_date date,
    amount_inr numeric(15,2),
    payment_method character varying(50),
    payment_status character varying(50)
);


--
-- Name: purchase_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.purchase_orders (
    po_id character varying(20) NOT NULL,
    vendor_id character varying(20),
    po_date date,
    category character varying(100),
    amount_inr numeric(15,2),
    status character varying(50)
);


--
-- Name: sales_invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sales_invoices (
    invoice_id character varying(20) NOT NULL,
    order_id character varying(20),
    customer_id character varying(20),
    invoice_date date,
    subtotal_inr numeric(15,2),
    tax_inr numeric(15,2),
    total_inr numeric(15,2),
    status character varying(50)
);


--
-- Name: sales_orders; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.sales_orders (
    order_id character varying(20) NOT NULL,
    customer_id character varying(20),
    order_date date,
    service_type character varying(100),
    origin character varying(100),
    destination character varying(100),
    order_value_inr numeric(15,2),
    discount_inr numeric(15,2),
    tax_inr numeric(15,2),
    status character varying(50)
);


--
-- Name: shipments; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.shipments (
    shipment_id character varying(20) NOT NULL,
    order_id character varying(20),
    carrier_id character varying(20),
    route_id character varying(20),
    warehouse_id character varying(20),
    pickup_date date,
    planned_delivery_date date,
    actual_delivery_date date,
    delivery_status character varying(50),
    delay_days integer,
    shipping_cost_inr numeric(15,2),
    fuel_cost_inr numeric(15,2),
    vehicle_id character varying(20),
    driver_id character varying(20)
);


--
-- Name: vendor_invoices; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vendor_invoices (
    vendor_invoice_id character varying(20) NOT NULL,
    po_id character varying(20),
    vendor_id character varying(20),
    invoice_date date,
    amount_inr numeric(15,2),
    status character varying(50)
);


--
-- Name: vendors; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.vendors (
    vendor_id character varying(20) NOT NULL,
    vendor_name character varying(150),
    contact_person character varying(100),
    email character varying(150),
    category character varying(100),
    products_services text,
    contract_id character varying(50),
    performance_score numeric(5,2),
    payment_terms_days integer,
    sla_hours integer
);


--
-- Name: business_rules business_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.business_rules
    ADD CONSTRAINT business_rules_pkey PRIMARY KEY (rule_id);


--
-- Name: company_master company_master_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.company_master
    ADD CONSTRAINT company_master_pkey PRIMARY KEY (company_id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (customer_id);


--
-- Name: documents documents_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.documents
    ADD CONSTRAINT documents_pkey PRIMARY KEY (document_id);


--
-- Name: emails emails_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.emails
    ADD CONSTRAINT emails_pkey PRIMARY KEY (message_id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (employee_id);


--
-- Name: events events_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.events
    ADD CONSTRAINT events_pkey PRIMARY KEY (event_id);


--
-- Name: expenses expenses_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.expenses
    ADD CONSTRAINT expenses_pkey PRIMARY KEY (expense_id);


--
-- Name: ingestion_test_business_rules ingestion_test_business_rules_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.ingestion_test_business_rules
    ADD CONSTRAINT ingestion_test_business_rules_pkey PRIMARY KEY (rule_id);


--
-- Name: payments payments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT payments_pkey PRIMARY KEY (payment_id);


--
-- Name: purchase_orders purchase_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT purchase_orders_pkey PRIMARY KEY (po_id);


--
-- Name: sales_invoices sales_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sales_invoices
    ADD CONSTRAINT sales_invoices_pkey PRIMARY KEY (invoice_id);


--
-- Name: sales_orders sales_orders_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sales_orders
    ADD CONSTRAINT sales_orders_pkey PRIMARY KEY (order_id);


--
-- Name: shipments shipments_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT shipments_pkey PRIMARY KEY (shipment_id);


--
-- Name: vendor_invoices vendor_invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT vendor_invoices_pkey PRIMARY KEY (vendor_invoice_id);


--
-- Name: vendors vendors_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vendors
    ADD CONSTRAINT vendors_pkey PRIMARY KEY (vendor_id);


--
-- Name: customers fk_customer_account_owner; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT fk_customer_account_owner FOREIGN KEY (account_owner_id) REFERENCES public.employees(employee_id);


--
-- Name: customers fk_customer_sales_rep; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT fk_customer_sales_rep FOREIGN KEY (sales_representative_id) REFERENCES public.employees(employee_id);


--
-- Name: employees fk_employee_manager; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT fk_employee_manager FOREIGN KEY (manager_id) REFERENCES public.employees(employee_id);


--
-- Name: sales_invoices fk_invoice_customer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sales_invoices
    ADD CONSTRAINT fk_invoice_customer FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: sales_invoices fk_invoice_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sales_invoices
    ADD CONSTRAINT fk_invoice_order FOREIGN KEY (order_id) REFERENCES public.sales_orders(order_id);


--
-- Name: payments fk_payment_invoice; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.payments
    ADD CONSTRAINT fk_payment_invoice FOREIGN KEY (invoice_id) REFERENCES public.sales_invoices(invoice_id);


--
-- Name: purchase_orders fk_purchase_order_vendor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.purchase_orders
    ADD CONSTRAINT fk_purchase_order_vendor FOREIGN KEY (vendor_id) REFERENCES public.vendors(vendor_id);


--
-- Name: sales_orders fk_sales_order_customer; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.sales_orders
    ADD CONSTRAINT fk_sales_order_customer FOREIGN KEY (customer_id) REFERENCES public.customers(customer_id);


--
-- Name: shipments fk_shipment_order; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.shipments
    ADD CONSTRAINT fk_shipment_order FOREIGN KEY (order_id) REFERENCES public.sales_orders(order_id);


--
-- Name: vendor_invoices fk_vendor_invoice_po; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT fk_vendor_invoice_po FOREIGN KEY (po_id) REFERENCES public.purchase_orders(po_id);


--
-- Name: vendor_invoices fk_vendor_invoice_vendor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.vendor_invoices
    ADD CONSTRAINT fk_vendor_invoice_vendor FOREIGN KEY (vendor_id) REFERENCES public.vendors(vendor_id);


--
-- PostgreSQL database dump complete
--

\unrestrict rYqRwnu7TM5dDlFgCWnHPVPEiDrZJiIWbuQUcGiM5sQkRqtFaXCq9EvhGzcb7OC

