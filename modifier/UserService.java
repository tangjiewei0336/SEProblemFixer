package com.example;

public class UserService {
    private UserDao userDao;

    public String getUserById(int id) {
        return userDao.findUser(id);
    }

    public void saveUser(User user) {
        userDao.save(user);
    }
}