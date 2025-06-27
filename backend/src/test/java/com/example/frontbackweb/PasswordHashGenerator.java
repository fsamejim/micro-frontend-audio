package com.example.frontbackweb;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordHashGenerator {
    public static void main(String[] args) {
        // This is the hash stored in the database (from data.sql)
        String storedHash = "$2a$10$DxDjxrTikQBAybXht4EgXuM1MsdbgSfoUkFqp0bD4Oo.KXq6ht5Uy";
        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        
        System.out.println("Simulating login password verification:");
        System.out.println("======================================");
        System.out.println("Stored hash in database: " + storedHash);
        
        // Simulate successful login
        String correctPassword = "admin123";
        System.out.println("\nTrying to login with correct password 'admin123':");
        System.out.println("Login successful? " + encoder.matches(correctPassword, storedHash));
        
        // Simulate failed login
        String wrongPassword = "wrongpassword";
        System.out.println("\nTrying to login with wrong password 'wrongpassword':");
        System.out.println("Login successful? " + encoder.matches(wrongPassword, storedHash));
        
        System.out.println("\nNote: During login verification:");
        System.out.println("1. The stored hash NEVER changes in the database");
        System.out.println("2. Spring Security extracts the salt from the stored hash");
        System.out.println("3. Uses that same salt to hash the entered password");
        System.out.println("4. Compares the results");
    }
} 