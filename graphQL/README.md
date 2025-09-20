# Week 1 API: GraphQL API with TypeScript, Apollo Server & Prisma (SQLite)

This project demonstrates a simple GraphQL API built using TypeScript, Apollo Server, and Prisma ORM with SQLite as the database.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/SoA-UET/Week1_API.git
   cd graphQL
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Set up the database**:
   - Run Prisma migrations to initialize the schema:
     ```bash
     npx prisma migrate dev --name init
     ```
   - Generate Prisma client:
     ```bash
     npx prisma generate
     ```
   - This will create a new SQLite database file (`dev.db`) in the `prisma` folder if it doesn't exist.

4. **Start the server**:
   ```bash
   npx ts-node src/index.ts
   ```
   The GraphQL server should now be running (typically at `http://localhost:4000`).

## Usage

Once the server is running, you can interact with the GraphQL API using tools like Apollo Studio, GraphQL Playground, or cURL/Postman.

### Example Queries

- **Get all users**:
  ```graphql
  query {
    users {
      id
      name
      age
    }
  }
  ```

- **Add a new user** (Mutation):
  ```graphql
  mutation {
    addUser(name: "Alice", age: 22) {
      id
      name
      age
    }
  }
  ```