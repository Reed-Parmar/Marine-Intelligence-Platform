-- Migration: Add 'molecular_edna' to public.dataset_domain enum
-- Description: Adds 'molecular_edna' to the dataset_domain PostgreSQL enum to align
-- with the frontend domain picker and eDNA pipeline.

ALTER TYPE public.dataset_domain ADD VALUE IF NOT EXISTS 'molecular_edna';
