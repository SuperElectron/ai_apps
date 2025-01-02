
__install supabase CLI__

- first, you need npm.  For other methods view the docs [here](https://supabase.com/docs/guides/local-development?queryGroups=package-manager&package-manager=npm).


```bash
$ curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
```

- Now we install the CLI.

```bash
$ npm install supabase --save-dev
```

__set up the code__

```bash
$ git clone https://github.com/supabase-community/vercel-ai-chatbot
```

- start supabase.  Note that there is a supabase folder in the directory.  Normally, this is created with `supabase init`, but it has been created for us.  Let's start supabase and check the API and ANON_KEY variables that will be used in our .env file in the next step

```bash
$ npm supabase start

Seeding globals from roles.sql...
Applying migration 20230707053030_init.sql...
Seeding data from seed.sql...
Started supabase local development setup.

         API URL: http://127.0.0.1:54321
     GraphQL URL: http://127.0.0.1:54321/graphql/v1
  S3 Storage URL: http://127.0.0.1:54321/storage/v1/s3
          DB URL: postgresql://postgres:postgres@127.0.0.1:54322/postgres
      Studio URL: http://127.0.0.1:54323
    Inbucket URL: http://127.0.0.1:54324
      JWT secret: super-secret-jwt-token-with-at-least-32-characters-long
        anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU
   S3 Access Key: 625729a08b95bf1b7ff351a663f3a23c
   S3 Secret Key: 850181e4652dd023b7a98c58ae0d2d34bd487ee0cc3254aed6eda37307425907
       S3 Region: local
A new version of Supabase CLI is available: v2.1.1 (currently installed v1.189.1)
We recommend updating regularly for new features and bug fixes: https://supabase.com/docs/guides/cli/getting-started#updating-the-supabase-cli

```

KEY THINGS TO TAKE NOTE OF

        1. API_URL
        API URL: http://127.0.0.1:54321
        - this is used in .env file.  All traffic goes through here.

        2. STUDIO
        Studio URL: http://127.0.0.1:54323
        - you can put this into your browser, upload a CSV of data into your database if you want.  It's great!

        3. ANON_KEY
        anon key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0
        - this is used in .env file.  

- set up your .env file (you'll need your own )

```bash
cp .env.example .env
```

- here is what we did for my variables above

```env
## You must first activate a Billing Account here: https://platform.openai.com/account/billing/overview
OPENAI_API_KEY=sk-proj-xxxxxx-get-your-own-key

# In local dev you can get these by running `supabase status`.
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

```

# Run

```bash
npm install
npm run dev
```

- now you can go to sign-up, and add a username and password.
- NOTE: it will tell you to confirm it in email (but we don't have email auth set up yet), so navigate to http://127.0.0.1:54323

    1. click authentication in side panel.
    2. Add a new user
    - add details and ensure 'auto confirm user' is selected
    3. now you can login with those credentials

- now navigate to your dashboard: http://localhost:3000 and login!

__tear down__

```bash
npm supabase stop
```