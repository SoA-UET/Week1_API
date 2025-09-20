import { gql } from "apollo-server";

export const typeDefs = gql`
  type User {
    id: ID!
    name: String!
    age: Int!
  }

  type Query {
    users: [User!]!
    hello: String!
  }

  type Mutation {
    addUser(name: String!, age: Int!): User!
  }
`;
