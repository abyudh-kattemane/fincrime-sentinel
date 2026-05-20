{{ config(materialized='view') }}
-- data source being used
with source as (
    select * from {{ source('ibm_aml', 'transactions') }}
),
-- staging logic
renamed as (
    select
        -- Identifiers
        from_bank::varchar || ':' || account_from::varchar  as src_account_id,
        to_bank::varchar   || ':' || account_to::varchar    as dst_account_id,

        -- Temporal
        timestamp                                            as txn_timestamp,
        date_trunc('day', timestamp)                         as txn_date,

        -- Amounts
        amount_paid                                          as amount,
        payment_currency                                     as currency,
        payment_format                                       as payment_method,

        -- Labels
        is_laundering::boolean                               as is_laundering

    from source
)
-- final selection
select * from renamed
