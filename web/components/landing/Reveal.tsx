"use client";

import React from "react";
import { motion, useReducedMotion, type Variants } from "framer-motion";

type Direction = "up" | "down" | "left" | "right" | "none";

const offsetFor = (direction: Direction, distance: number) => {
  switch (direction) {
    case "up":
      return { y: distance };
    case "down":
      return { y: -distance };
    case "left":
      return { x: distance };
    case "right":
      return { x: -distance };
    default:
      return {};
  }
};

type RevealProps = {
  children: React.ReactNode;
  className?: string;
  direction?: Direction;
  delay?: number;
  distance?: number;
  duration?: number;
  once?: boolean;
  as?: keyof typeof motion;
};

export default function Reveal({
  children,
  className,
  direction = "up",
  delay = 0,
  distance = 28,
  duration = 0.7,
  once = true,
}: RevealProps) {
  const reduce = useReducedMotion();

  const variants: Variants = {
    hidden: reduce ? { opacity: 0 } : { opacity: 0, ...offsetFor(direction, distance) },
    visible: {
      opacity: 1,
      x: 0,
      y: 0,
      transition: {
        duration: reduce ? 0.2 : duration,
        delay: reduce ? 0 : delay,
        ease: [0.21, 0.47, 0.32, 0.98],
      },
    },
  };

  return (
    <motion.div
      className={className}
      variants={variants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: "-80px" }}
    >
      {children}
    </motion.div>
  );
}

type StaggerProps = {
  children: React.ReactNode;
  className?: string;
  delayChildren?: number;
  staggerChildren?: number;
  once?: boolean;
};

export function Stagger({
  children,
  className,
  delayChildren = 0.05,
  staggerChildren = 0.1,
  once = true,
}: StaggerProps) {
  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, margin: "-80px" }}
      variants={{
        hidden: {},
        visible: {
          transition: { delayChildren, staggerChildren },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

type StaggerItemProps = {
  children: React.ReactNode;
  className?: string;
  direction?: Direction;
  distance?: number;
};

export function StaggerItem({
  children,
  className,
  direction = "up",
  distance = 24,
}: StaggerItemProps) {
  const reduce = useReducedMotion();

  const variants: Variants = {
    hidden: reduce ? { opacity: 0 } : { opacity: 0, ...offsetFor(direction, distance) },
    visible: {
      opacity: 1,
      x: 0,
      y: 0,
      transition: { duration: reduce ? 0.2 : 0.6, ease: [0.21, 0.47, 0.32, 0.98] },
    },
  };

  return (
    <motion.div className={className} variants={variants}>
      {children}
    </motion.div>
  );
}
