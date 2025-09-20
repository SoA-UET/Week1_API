import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export const resolvers = {
  Query: {
    hello: () => "Hello GraphQL + TypeScript + Prisma 🚀",
    users: async () => await prisma.user.findMany(),
  },
  Mutation: {
    addUser: async (_: any, args: { name: string; age: number }) => {
      return await prisma.user.create({
        data: {
          name: args.name,
          age: args.age,
        },
      });
    },
  },
};
